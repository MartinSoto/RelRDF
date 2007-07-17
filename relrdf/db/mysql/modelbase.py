import string

import MySQLdb
from  sqlalchemy import pool

from relrdf.expression import uri
from relrdf.util.methodsync import SyncMethodsMixin, synchronized

import basicquery
import basicsinks


class ModelBase(SyncMethodsMixin):
    __slots__ = ('host',
                 'db',
                 'mysqlParams',
                 'querySchema',
                 'sinkSchema',

                 '_connPool',
                 '_connection',
                 '_prefixes',
                 '_twoWayUsers',
                 '_threeWayUsers',)

    def __init__(self, host, db, **mysqlParams):
        super(ModelBase, self).__init__()

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

        # The control connection. Public methods using it must be
        # synchronized.
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
        self._connection.commit()

        # Number of models using two and three-way comparisons.
        self._twoWayUsers = {}
        self._threeWayUsers = {}

        # Any uses present in the database that are associated to this
        # connection's id must come from an older connection that
        # didn't clean-up properly. Clean up them now.
        self._cleanUpUses()

    def _cleanUpUses(self):
        """Clean up all uses associated to this connection."""
        cursor = self._connection.cursor()
        cursor.execute("""
            DELETE FROM twoway_conns
            WHERE connection = connection_id()
            """)
        cursor.execute("""
            DELETE FROM threeway_conns
            WHERE connection = connection_id()
            """)
        cursor.close()
        self._connection.commit()

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

    _updateTimeTwoWay = string.Template(
        """
        INSERT INTO twoway_use_time (version_a, version_b, time)
        VALUES ($versionA, $versionB, now())
        ON DUPLICATE KEY UPDATE time = now()
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

    _connTwoWay = string.Template(
        """
        INSERT INTO twoway_conns (version_a, version_b, connection)
        VALUES ($versionA, $versionB, connection_id())
        """)

    @synchronized
    def prepareTwoWay(self, versionA, versionB, refreshComp=False):
        count = self._twoWayUsers.get((versionA, versionB))
        if count is not None:
            # This comparison model was already used by the model base
            # and should still be in the cache.
            count += 1
            self._twoWayUsers[(versionA, versionB)] = count
            return
        else:
            self._twoWayUsers[(versionA, versionB)] = 1

        cursor = self._connection.cursor()

        # Update the use time.
        cursor.execute(self._updateTimeTwoWay.substitute(versionA=versionA,
                                                         versionB=versionB))

        # Check if a comparison model for these versions is already
        # there. According to the MySQL rules, the rowcount is 1 if a
        # new row was inserted, but 2 if it was updated.
        if cursor.rowcount == 1 or refreshComp:
            if refreshComp:
                # Clean up any existing comparison data.
                cursor.execute(self._deleteTwoWay \
                               .substitute(versionA=versionA,
                                           versionB=versionB))

            # Calculate the comparison model.
            cursor.execute(self._createTwoWay.substitute(versionA=versionA,
                                                         versionB=versionB))

        # Register the control connection as a user for this
        # comparison.
        cursor.execute(self._connTwoWay.substitute(versionA=versionA,
                                                   versionB=versionB))

        self._connection.commit()
        cursor.close()

    @synchronized
    def releaseTwoWay(self, versionA, versionB):
        count = self._twoWayUsers[(versionA, versionB)]
        assert count > 0
        count -= 1
        self._twoWayUsers[(versionA, versionB)] = count

    _updateTimeThreeWay = string.Template(
        """
        INSERT INTO threeway_use_time (version_a, version_b, version_c, time)
        VALUES ($versionA, $versionB, $versionC, now())
        ON DUPLICATE KEY UPDATE time = now()
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

    _connThreeWay = string.Template(
        """
        INSERT INTO threeway_conns (version_a, version_b, version_c,
                                    connection)
        VALUES ($versionA, $versionB, $versionC, connection_id())
        """)

    @synchronized
    def prepareThreeWay(self, versionA, versionB, versionC,
                        refreshComp=False):
        count = self._threeWayUsers.get((versionA, versionB, versionC))
        if count is not None:
            # This comparison model was already used by the model base
            # and should still be in the cache.
            count += 1
            self._threeWayUsers[(versionA, versionB, versionC)] = count
            return
        else:
            self._threeWayUsers[(versionA, versionB, versionC)] = 1

        cursor = self._connection.cursor()

        # Update the use time.
        cursor.execute(self._updateTimeThreeWay.substitute(versionA=versionA,
                                                           versionB=versionB,
                                                           versionC=versionC))

        # Check if a comparison model for these versions is already
        # there. According to the MySQL rules, the rowcount is 1 if a
        # new row was inserted, but 2 if it was updated.
        if cursor.rowcount == 1 or refreshComp:
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
            
        # Register the control connection as a user for this
        # comparison.
        cursor.execute(self._connThreeWay.substitute(versionA=versionA,
                                                     versionB=versionB,
                                                     versionC=versionC))

        self._connection.commit()
        cursor.close()

    @synchronized
    def releaseThreeWay(self, versionA, versionB, versionC):
        count = self._threeWayUsers[(versionA, versionB, versionC)]
        assert count > 0
        count -= 1
        self._threeWayUsers[(versionA, versionB, versionC)] = count

    @synchronized
    def close(self):
        self._cleanUpUses()

        # Close the control connection.
        self._connection.close()


def getModelBase(**modelBaseArgs):
    return ModelBase(**modelBaseArgs)
