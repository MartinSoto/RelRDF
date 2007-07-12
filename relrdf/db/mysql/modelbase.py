import MySQLdb

import basicquery
import basicsinks


class ModelBase(object):
    __slots__ = ('host',
                 'db',
                 'mysqlParams',
                 'querySchema',
                 'sinkSchema')

    def __init__(self, host, db, **mysqlParams):
        # We have only one database schema at this time.
        self.sinkSchema = basicsinks
        self.querySchema = basicquery

        self.host = host
        self.db = db
        self.mysqlParams = mysqlParams

    def createConnection(self):
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

    def getSink(self, sinkType, **sinkArgs):
        return self.sinkSchema.getSink(self.createConnection(),
                                       sinkType, **sinkArgs)

    def getModel(self, modelType, **modelArgs):
        return self.querySchema.getModel(self, modelType, **modelArgs)

    def close(self):
        pass


def getModelBase(**modelBaseArgs):
    return ModelBase(**modelBaseArgs)
