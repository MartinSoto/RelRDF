import string

import MySQLdb
from  sqlalchemy import pool

from relrdf.expression import uri

import basicquery
import basicsinks


class ModelBase(object):
    __slots__ = ('host',
                 'db',
                 'mysqlParams',
                 'querySchema',
                 'sinkSchema',

                 '_connPool',
                 '_connection',
                 '_prefixes',)

    def __init__(self, host, db, **mysqlParams):
        import sys

        # We have only one database schema at this time.
        self.sinkSchema = basicsinks
        self.querySchema = basicquery

        self.host = host
        self.db = db
        self.mysqlParams = mysqlParams

        # Create the connection pool.
        self._connPool = pool.QueuePool(self._setupConnection,
                                        pool_size=5,
                                        use_threadlocal=False)

        # Create the control connection.
        self._connection = self.createConnection()

        # Get the prefixes from the database:

        cursor = self._connection.cursor()
        cursor.execute("""
            SELECT p.prefix, p.namespace
            FROM prefixes p
            """)

        self._prefixes = {}

        row = cursor.fetchone()
        while row is not None:
            (prefix, namespace) = row
            self._prefixes[prefix] = uri.Namespace(namespace)
            row = cursor.fetchone()

        cursor.close()

    def _setupConnection(self):
        connection = MySQLdb.connect(host=self.host, db=self.db,
                                     **self.mysqlParams)

        # Set the connection's character set to unicode.
        connection.set_character_set('utf8')

        # This is necessary for complex queries to run at all. Due to
        # the large number of joins, queries with more than about 10
        # patterns take a very long time to optimize.
        cursor = connection.cursor()
        cursor.execute('SET optimizer_search_depth = 0')
        cursor.close()

        return connection

    def createConnection(self):
        return self._connPool.connect()

    def getSink(self, sinkType, **sinkArgs):
        return self.sinkSchema.getSink(self.createConnection(),
                                       sinkType, **sinkArgs)

    def getModel(self, modelType, **modelArgs):
        return self.querySchema.getModel(self, modelType, **modelArgs)

    def getPrefixes(self):
        return self._prefixes

    _countTwoWay = string.Template(
        """
        SELECT count(*)
        FROM twoway t
        WHERE t.version_a = $versionA AND t.version_b = $versionB
        """)

    _deleteTwoWay = string.Template(
        """
        DELETE FROM twoway
        WHERE version_a = $versionA AND version_b = $versionB
        """)

    # Query for calculating the two-way comparison model. This is a
    # pretty sui generis way of performing the actual comparison, but
    # MySQL doesn't have a full outer join, and this solution not only
    # works properly but seems to be very efficient. Notice that it
    # relies on the fact that version numbers are never 0. The IF
    # expressions inside the sum are necessary to guarantee correct
    # results when versionA and versionB are equal.
    _createTwoWay = string.Template(
        """
        INSERT INTO twoway (version_a, version_b, stmt_id, context)
          SELECT
            $versionA AS version_a,
            $versionB AS version_b,
            v.stmt_id AS stmt_id,
            CASE sum(IF(v.version_id = $versionA, 1, 0) +
                     IF(v.version_id = $versionB, 2, 0))
              WHEN 1 THEN "A"
              WHEN 2 THEN "B"
              WHEN 3 THEN "AB"
            END AS context
          FROM version_statement v
          WHERE v.version_id = $versionA or v.version_id = $versionB
          GROUP BY v.stmt_id
        """)

    def prepareTwoWay(self, versionA, versionB, refreshComp=False):
        cursor = self._connection.cursor()

        # Check if a comparison model for these versions is already
        # there.
        cursor.execute(self._countTwoWay.substitute(versionA=versionA,
                                                    versionB=versionB))

        if cursor.fetchone()[0] == 0 or refreshComp:
            if refreshComp:
                # Clean up any existing comparison data.
                cursor.execute(self._deleteTwoWay \
                               .substitute(versionA=versionA,
                                           versionB=versionB))

            # Calculate the comparison model.
            cursor.execute(self._createTwoWay.substitute(versionA=versionA,
                                                         versionB=versionB))

            self._connection.commit()
            
        cursor.close()

    def releaseTwoWay(self, versionA, versionB):
        pass

    _countThreeWay = string.Template(
        """
        SELECT count(*)
        FROM threeway t
        WHERE t.version_a = $versionA AND t.version_b = $versionB AND
              t.version_c = $versionC
        """)

    _deleteThreeWay = string.Template(
        """
        DELETE FROM threeway
        WHERE version_a = $versionA AND version_b = $versionB AND
              version_c = $versionC
        """)

    # Query for calculating the three-way comparison model. See the
    # comment for _createTwoWay
    _createThreeWay = string.Template(
        """
        INSERT INTO threeway (version_a, version_b, version_c,
                              stmt_id, context)
          SELECT
            $versionA AS version_a,
            $versionB AS version_b,
            $versionC AS version_c,
            v.stmt_id AS stmt_id,
            CASE
                sum(IF(v.version_id = $versionA, 1, 0) +
                    IF(v.version_id = $versionB, 2, 0) +
                    IF(v.version_id = $versionC, 4, 0))
              WHEN 1 THEN "A"
              WHEN 2 THEN "B"
              WHEN 3 THEN "AB"
              WHEN 4 THEN "C"
              WHEN 5 THEN "AC"
              WHEN 6 THEN "BC"
              WHEN 7 THEN "ABC"
            END AS context
          FROM version_statement v
          WHERE v.version_id = $versionA or v.version_id = $versionB
                or v.version_id = $versionC
          GROUP BY v.stmt_id
        """)

    def prepareThreeWay(self, versionA, versionB, versionC,
                        refreshComp=False):
        cursor = self._connection.cursor()

        # Check if a comparison model for these versions is already
        # there.
        cursor.execute(self._countThreeWay.substitute(versionA=versionA,
                                                      versionB=versionB,
                                                      versionC=versionC))

        if cursor.fetchone()[0] == 0 or refreshComp:
            if refreshComp:
                # Clean up any existing comparison data.
                cursor.execute(self._deleteThreeWay \
                               .substitute(versionA=versionA,
                                           versionB=versionB,
                                           versionC=versionC))

            # Calculate the comparison model.
            cursor.execute(self._createThreeWay.substitute(versionA=versionA,
                                                           versionB=versionB,
                                                           versionC=versionC))

            self._connection.commit()
            
        cursor.close()

    def releaseThreeWay(self, versionA, versionB, versionC):
        pass

    def close(self):
        # Close de control connection.
        self._connection.close()


def getModelBase(**modelBaseArgs):
    return ModelBase(**modelBaseArgs)
