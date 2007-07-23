import MySQLdb

import basicquery
import basicsinks


class ModelBase(object):
    __slots__ = ('connection',
                 'querySchema',
                 'sinkSchema')

    name = "MySQL"
    parameterInfo = ({"name":"host",   "label":"Database Host", "tip":"Enter the name or the IP-Address of the database host", "default":"localhost", "assert":"host!=''", "asserterror":"host must not be empty"},
                     {"name":"user",   "label":"Username",      "tip":"Enter the username required to log into your database", "assert":"user!=''", "asserterror":"username must not be empty"},
                     {"name":"passwd", "label":"Password",      "tip":"Enter the password required to log into your database", "hidden":True},
                     {"name":"db",     "label":"Database",      "tip":"Enter the name of the database to open or leave blank for default", "omit":"db==''"})
    @classmethod
    def getModelInfo(self, **parameters):
        return basicquery._modelFactories
    
    def __init__(self, host, db, **mysqlParams):
        self.connection = MySQLdb.connect(host=host, db=db, **mysqlParams)

        # Set the connection´s character set to unicode.
        self.connection.set_character_set('utf8')

        # This is necessary for complex queries to run at all. Due to
        # the large number of joins, queries with more than about 10
        # patterns take a very long time to optimize.
        cursor = self.connection.cursor()
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
