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
        # database to send results back un UTF-8.
        cursor = self.connection.cursor()
        cursor.execute('SET character_set_results = utf8')
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


def getModelBase(**modelBaseArgs):
    return ModelBase(**modelBaseArgs)
