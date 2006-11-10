from pysqlite2 import dbapi2 as sqlite

import basicquery
import basicsinks


class ModelBase(object):
    __slots__ = ('connection',
                 'querySchema',
                 'sinkSchema')

    def __init__(self, dbFileName, **sqliteParams):
        self.connection = sqlite.connect(dbFileName)

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
