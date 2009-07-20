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


import string

import pgdb
from  sqlalchemy import pool

from relrdf.localization import _
from relrdf import error
from relrdf.expression import uri
from relrdf.util.methodsync import SyncMethodsMixin, synchronized
from relrdf.util.nsshortener import NamespaceUriShortener
from relrdf import commonns

import basicquery
import basicsinks

class ModelBase(SyncMethodsMixin):
    __slots__ = ('db',
                 'params',
                 'querySchema',
                 'sinkSchema',

                 '_connPool',
                 '_connection',
                 '_prefixes',)

    name = "PostgreSQL"
    parameterInfo = ({"name":"host",    "label":"Database Host", "tip":"Enter the name or the IP-Address of the database host", "default":"localhost", "assert":"host!=''", "asserterror":"host must not be empty"},
                     {"name":"user",    "label":"Username",      "tip":"Enter the username required to log into your database", "assert":"user!=''", "asserterror":"username must not be empty"},
                     {"name":"password","label":"Password",      "tip":"Enter the password required to log into your database", "hidden":True},
                     {"name":"database","label":"Database",      "tip":"Enter the name of the database to open or leave blank for default", "omit":"db==''"})

    @classmethod
    def getModelInfo(self, **parameters):
        return basicquery.getModelMappers()

    def __init__(self, db, **params):
        super(ModelBase, self).__init__()

        import sys

        # We have only one database schema at this time.
        self.sinkSchema = basicsinks
        self.querySchema = basicquery

        self.db = db
        self.params = params

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

        self._prefixes = NamespaceUriShortener()

        row = cursor.fetchone()
        while row is not None:
            (prefix, namespace) = row
            self._prefixes[prefix] = uri.Namespace(namespace)
            row = cursor.fetchone()

        cursor.close()
        self._connection.commit()

    def _setupConnection(self):

        connection = pgdb.connect(database=self.db, **self.params)

        return connection

    def createConnection(self):
        return self._connPool.connect()

    def getSink(self, sinkType, **sinkArgs):
        return self.sinkSchema.getSink(self, self.createConnection(), sinkType, **sinkArgs)

    def getModel(self, modelType, **modelArgs):
        return self.querySchema.getModel(self, self.createConnection(), modelType, **modelArgs)

    def getPrefixes(self):
        return self._prefixes

    def lookupGraphId(self, graphUri, connection=None, create=False):

        # Normalize URI
        graphUri = self._prefixes.normalizeUri(graphUri).encode('utf-8')

        # Create connection and get cursor
        ownConnection = False
        if connection is None:
            connection = self.createConnection()
            ownConnection = True
        cursor = connection.cursor()

        # Try lookup
        cursor.execute("""SELECT graph_id FROM graphs WHERE graph_uri = '%s';""" % graphUri)
        result = cursor.fetchone()
        if not result is None:
            return result[0]

        # Should not create? Return ID of an empty graph
        # (graph IDs normally start at 1)
        if not create:
            return 0

        # Insert new graph
        cursor.execute("INSERT INTO graphs (graph_uri) VALUES ('%s') RETURNING graph_id;" % graphUri)
        result = cursor.fetchone()
        assert not result is None, "Could not create a new graph!"

        # Commit
        if ownConnection:
            connection.commit()

        # Done
        return result[0]

    def prepareTwoWay(self, graphA, graphB):
        cursor = self._connection.cursor()

        # Create comparison graphs
        baseGraphName = "cmp_%d_%d_" % (graphA, graphB)
        graphUris = [commonns.relrdf[baseGraphName + suffix + '#'] for suffix in ('A', 'B', 'AB')]
        graphs = [self.lookupGraphId(uri, create=True) for uri in graphUris]

        # Clear previous data
        cursor.execute("DELETE FROM graph_statement WHERE graph_id IN (%d, %d, %d)" % (graphs[0], graphs[1], graphs[2]));

        # Insert data
        cursor.execute(
             """
             INSERT INTO graph_statement (stmt_id, graph_id)
               SELECT COALESCE(a.stmt_id, b.stmt_id),
                      CASE WHEN a.stmt_id IS NULL THEN %d
                           WHEN b.stmt_id IS NULL THEN %d
                           ELSE %d END
               FROM (SELECT stmt_id FROM graph_statement WHERE graph_id = %d) AS a FULL JOIN
                    (SELECT stmt_id FROM graph_statement WHERE graph_id = %d) AS b
                    ON a.stmt_id = b.stmt_id
             """ % (graphs[0], graphs[1], graphs[2], graphA, graphB))

        self._connection.commit()
        return graphUris

    @synchronized
    def close(self):

        # Close the control connection.
        self._connection.close()


def getModelBase(**modelBaseArgs):
    return ModelBase(**modelBaseArgs)
