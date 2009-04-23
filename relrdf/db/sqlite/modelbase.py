# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2009 Fraunhofer-Institut fuer Experimentelles
#                         Software Engineering (IESE).
#
# RelRDF is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA. 


from pysqlite2 import dbapi2 as sqlite

import basicquery
import basicsinks


class ModelBase(object):
    __slots__ = ('connection',
                 'querySchema',
                 'sinkSchema')

    name = "SQLite"
    parameterInfo = ({"name":"host",   "label":"Database Host", "tip":"Enter the name or the IP-Address of the database host", "default":"localhost", "assert":"host!=''", "asserterror":"host must not be empty"},
                     {"name":"user",   "label":"Username",      "tip":"Enter the username required to log into your database", "assert":"user!=''", "asserterror":"username must not be empty"},
                     {"name":"passwd", "label":"Password",      "tip":"Enter the password required to log into your database", "hidden":True},
                     {"name":"db",     "label":"Database",      "tip":"Enter the name of the database to open or leave blank for default", "omit":"db==''"})
    modelInfo = basicquery._modelFactories

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
