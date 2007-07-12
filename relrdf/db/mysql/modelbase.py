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
                                        use_threadlocal=True)

        # Get the prefixes from the database:

        conn = self.createConnection()
        cursor = conn.cursor()
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
        conn.close()

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

    def close(self):
        pass


def getModelBase(**modelBaseArgs):
    return ModelBase(**modelBaseArgs)
