import MySQLdb

import basicschema


class ModelBase(object):
    __slots__ = ('connection',
                 'dbSchema')

    def __init__(self, host, db, **mysqlParams):
        self.connection = MySQLdb.connect(host=host, db=db, **mysqlParams)

        # Set the connection's character encoding to UTF-8.
        cursor = self.connection.cursor()
        cursor.execute('set names "utf8"')
        cursor.close()

        # We have only one database schema at this time.
        self.dbSchema = basicschema

    def getModel(self, modelType, **modelArgs):
        return self.dbSchema.getModel(self.connection,
                                      modelType,
                                      **modelArgs)


def getModelBase(**modelBaseArgs):
    return ModelBase(**modelBaseArgs)
