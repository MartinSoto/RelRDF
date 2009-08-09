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

from relrdf.localization import _
from relrdf import error
from relrdf.error import InstantiationError
from relrdf.expression import uri, literal
from relrdf.util.nsshortener import NamespaceUriShortener
from relrdf import commonns

import basicquery
import basicsinks

class BasicModelBase(object):
    """Model base for the basic schema."""

    __slots__ = ('db',
                 'verbose',

                 '_prefixes',
                 '_connection',
                 '_modifCursor',
                 '_deleting',
                 '_pendingRows')

    # Maximum number of rows per insert query.
    ROWS_PER_QUERY = 10000

    name = "PostgreSQL (basic schema)"
    parameterInfo = ({"name": "host",
                      "label": "Database Host",
                      "tip": "Enter the name or the IP-Address of the "
                      "database host",
                      "default": "localhost",
                      "assert": "host!=''",
                      "asserterror": "host must not be empty"},
                     {"name": "user",
                      "label": "Username",
                      "tip": "Enter thn---e username required to log "
                      "into your database",
                      "assert": "user!=''",
                      "asserterror": "username must not be empty"},
                     {"name": "password",
                      "label": "Password",
                      "tip": "Enter the password required to log into "
                      "your database",
                      "hidden": True},
                     {"name": "database",
                      "label": "Database",
                      "tip": "Enter the name of the database to open or "
                      "leave blank for default",
                      "omit": "db==''"})

    @classmethod
    def getModelInfo(self, **parameters):
        return basicquery.getModelMappers()

    def __init__(self, db, verbose=False, **params):
        self.db = db
        self.verbose = verbose

        # Create the connection.
        self._connection = pgdb.connect(database=self.db, **params)

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

        # Prepare for database modification.
        self._modifCursor = self._connection.cursor()
        self._modifSetup()

    def lookupGraphId(self, graphUri, create=False):
        # Normalize URI
        graphUri = self._prefixes.normalizeUri(graphUri).encode('utf-8')

        # Get a cursor.
        cursor = self._connection.cursor()

        # Lookup the graph.
        cursor.execute("""
            SELECT graph_id
            FROM graphs
            WHERE graph_uri = '%s';""" % graphUri)
        result = cursor.fetchone()
        if not result is None:
            return result[0]

        # Should not create? Return ID of an empty graph
        # (graph IDs normally start at 1).
        if not create:
            return 0

        # Insert new graph.
        cursor.execute("""
            INSERT INTO graphs (graph_uri)
            VALUES ('%s')
            RETURNING graph_id;""" % graphUri)
        result = cursor.fetchone()
        assert not result is None, "Could not create a new graph!"

        # Done.
        return result[0]


    #
    # Basic model base functions
    #

    def getSink(self, sinkType, **sinkArgs):
        return basicsinks.getSink(self, sinkType, **sinkArgs)

    def getModel(self, modelType, **modelArgs):
        return basicquery.getModel(self, self._connection, modelType,
                                   **modelArgs)

    def getPrefixes(self):
        return self._prefixes


    #
    # Modification related methods
    #

    def _modifSetup(self):
        """Set up the connection for database modification."""
        # Create a temporary table to hold the results.
        self._modifCursor.execute("""
            CREATE TEMPORARY TABLE statements_temp1 (
              graph_id integer,
              subject rdf_term,
              predicate rdf_term,
              object rdf_term
            )
            ON COMMIT DROP;
            """)

        self._pendingRows = []

        # As long as there are no statements in _pendingRows, we are
        # neither deleting nor inserting.
        self._deleting = None

    def queueTriple(self, graphId, delete, subject, pred, object):
        assert isinstance(subject, uri.Uri)
        assert isinstance(pred, uri.Uri)

        # Prepare the components for the object, which can be a
        # literal:

        lang = typeUri = None
        isResource = 0
        if isinstance(object, uri.Uri):
            isResource = 1
        elif isinstance(object, literal.Literal):
            if not object.typeUri is None:
                typeUri = unicode(object.typeUri).encode('utf-8')
            elif not object.lang is None:
                lang = unicode(object.lang.lower()).encode('utf-8')
        else:
            assert False, "Unexpected object type '%d'" \
                   % object.__class__.__name__

        delete = bool(delete)
        if self._deleting is None:
            self._deleting = delete
        elif self._deleting != delete:
            # We are changing from inserting to deleting or vice
            # versa.
            self.flush()
            self._deleting = delete

        # Collect the row.
        self._pendingRows.append((graphId,
                                  unicode(subject).encode('utf-8'),
                                  unicode(pred).encode('utf-8'),
                                  unicode(object).encode('utf-8'),
                                  isResource, typeUri, lang))

        if len(self._pendingRows) >= self.ROWS_PER_QUERY:
            self._writePendingRows()

    def insertByQuery(self, graphId, stmtQuery, stmtsPerRow):
        # Get rid of any pending rows.
        self.flush()

        # Collect needed columns.
        columns = ["col_%d" % i for i in range(3*stmtsPerRow)]
        colDecls = ["%s rdf_term" % c for c in columns]

        # Create temporary table to receive the results.
        self._modifCursor.execute("""
            CREATE TEMPORARY TABLE statements_temp_qry (%s) ON COMMIT DROP;
            """ % ','.join(colDecls))

        # Insert data.
        self._modifCursor.execute("INSERT INTO statements_temp_qry (%s);" %
                            stmtQuery)

        # Move data into main data table.
        for i in range(stmtsPerRow):
            self._modifCursor.execute("""
                INSERT INTO
                  statements_temp1 (graph_id, subject, predicate, object)
                SELECT %d, col_%d, col_%d, col_%d
                FROM statements_temp_qry""" % (graphId,
                                               i*3+0, i*3+1, i*3+2))

        # Drop intermediate table.
        self._modifCursor.execute("DROP TABLE statements_temp_qry;")

        # Move the data to its final destination.
        self.flush()

    def _writePendingRows(self):
        if self.verbose:
            print "Inserting %d rows..." % (len(self._pendingRows))

        self._modifCursor.executemany("""
            INSERT INTO statements_temp1 (graph_id, subject, predicate,
                                          object)
            VALUES (
              %d,
              rdf_term(0, %s),
              rdf_term(0, %s),
              rdf_term_create(%s, %d, %s, %s))""",
            self._pendingRows)

        self._pendingRows = []
        self._deleting = None

    def flush(self):
        """Perform all pending operations.

        This involves both sending data cached in memory to the
        database, and processing all data stored in temporary
        structures in the database itself. This operation does not
        perform a commit."""

        if len(self._pendingRows) == 0:
            return

        self._writePendingRows()

        # Delete?
        if self._deleting:
            # Remove existing statements.
            if self.verbose:
                print "Removing statements from graph...",
            self._modifCursor.execute("""
                DELETE FROM graph_statement gs
                USING  statements s, statements_temp1 st
                WHERE s.subject = st.subject AND
                      s.predicate = st.predicate AND
                      s.object = st.object AND
                      gs.stmt_id = s.id AND
                      gs.graph_id = st.graph_id
                """)
            if self.verbose:
                print "%d removed" % self._modifCursor.rowcount

            # Note: This is a /lot/ more efficient than
            # "... WHERE id NOT IN (SELECT stmt_id FROM statements)"
            if self.verbose:
                print "Removing unused statements..."
            self._modifCursor.execute("""
                DELETE FROM statements
                USING statements ss LEFT JOIN graph_statement gs
                      ON gs.stmt_id = ss.id
                WHERE gs.stmt_id IS NULL);
                """)
            if self.verbose:
                print "%d removed" % self._modifCursor.rowcount

        else:
            if self.verbose:
                print "Inserting statements...",
            self._modifCursor.execute("""
                SELECT insert_statements();
                """)
            if self.verbose:
                print "%s new" % self._modifCursor.fetchone()[0]

        # Drop statements.
        self._modifCursor.execute("""
            TRUNCATE TABLE statements_temp1
            """)


    #
    # Comparison
    #

    def prepareTwoWay(self, graphA, graphB):
        cursor = self._connection.cursor()

        # Create comparison graphs
        baseGraphName = "cmp_%d_%d_" % (graphA, graphB)
        graphUris = [commonns.relrdf[baseGraphName + suffix + '#']
                     for suffix in ('A', 'B', 'AB')]
        graphs = [self.lookupGraphId(uri, create=True) for uri in graphUris]

        # Clear previous data
        cursor.execute("""
            DELETE FROM graph_statement
            WHERE graph_id
            IN (%d, %d, %d)""" % (graphs[0], graphs[1], graphs[2]));

        # Insert data
        cursor.execute("""
             INSERT INTO graph_statement (stmt_id, graph_id)
               SELECT COALESCE(a.stmt_id, b.stmt_id),
                      CASE WHEN a.stmt_id IS NULL THEN %d
                           WHEN b.stmt_id IS NULL THEN %d
                           ELSE %d END
               FROM (SELECT stmt_id
                     FROM graph_statement
                     WHERE graph_id = %d) AS a
                    FULL JOIN
                    (SELECT stmt_id
                     FROM graph_statement
                     WHERE graph_id = %d) AS b
                    ON a.stmt_id = b.stmt_id
             """ % (graphs[0], graphs[1], graphs[2], graphA, graphB))

        return graphUris


    #
    # Transaction management
    #

    def rollback(self):
        self._connection.rollback()

        self._modifSetup()

    def commit(self):
        self.flush()

        self._connection.commit()

        if self.verbose:
            print "All done!"

    def close(self):
        # Changes must be explicitly committed.
        self.rollback()

        # Close the connection.
        self._modifCursor.close()
        self._connection.close()


def checkSchemaVersion(name, version, minVer, maxVer):
    if version < minVer:
        raise InstantiationError(_("Version %d of schema '%s' is too old "
                                   "for this version of RelRDF. You probably "
                                   "need to upgrade your schema or use an "
                                   "older version of RelRDF") %
                                 (version, name))
    if version > maxVer:
        raise InstantiationError(_("Version %d of schema '%s' is not "
                                   "supported by this version of RelRDF. "
                                   "You probably need to upgrade your "
                                   "RelRDF installation") %
                                 (version, name))

def getModelBase(db, **modelBaseArgs):
    # FIXME: This will cause slowness in situations where many
    # model bases must be created (e.g., Internet server).
    conn = pgdb.connect(database=db, **modelBaseArgs)

    cursor = conn.cursor()
    cursor.execute("select name, version from relrdf_schema_version")
    name, version = cursor.fetchone()
    cursor.close()

    conn.close()

    if name == 'basic':
        checkSchemaVersion(name, version, 1, 1)
        return BasicModelBase(db, **modelBaseArgs)
    else:
        raise InstantiationError(_("Unsupported schema '%s'") % name)
