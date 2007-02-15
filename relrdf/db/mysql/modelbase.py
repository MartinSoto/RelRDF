import MySQLdb

import basicquery
import basicsinks


class ModelBase(object):
    __slots__ = ('connection',
                 'querySchema',
                 'sinkSchema')

    def __init__(self, host, db, **mysqlParams):
        self.connection = MySQLdb.connect(host=host, db=db, **mysqlParams)

        # MySQLdb seems to send queries correctly to the server, but
        # it doesn't decode the results accordingly. We tell the
        # database to send results back in UTF-8.
        cursor = self.connection.cursor()

        # Set the result character set to unicode. Changing it
        # generally using "SET names" causes problems with MySQLdb and
        # queries containing non-ASCII characters.
        cursor.execute('SET character_set_results = utf8')

        # This is necessary for complex queries to run at all. Due to
        # the large the number of joins, queries with more than about
        # 10 patterns take a very long time to optimize.
        cursor.execute('SET optimizer_search_depth = 0')
        cursor.close()

        # We have only one database schema at this time.
        self.sinkSchema = basicsinks
        self.querySchema = basicquery

    def getSink(self, sinkType, **sinkArgs):
        return self.sinkSchema.getSink(self.connection,
                                       sinkType,
                                       **sinkArgs)

    def getModel(self, modelType, **modelArgs):
        return self.querySchema.getModel(self.connection,
                                         modelType,
                                         **modelArgs)

    def close(self):
        self.connection.close()


def getModelBase(**modelBaseArgs):
    return ModelBase(**modelBaseArgs)
