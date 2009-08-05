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


from relrdf.error import InstantiationError
from relrdf.expression import uri, literal
from relrdf import commonns

class SingleGraphRdfSink(object):
    """An RDF sink that sends all tuples to a single graph in the
    database."""

    __slots__ = ('modelBase',
                 'connection',
                 'cursor',
                 'baseGraph',
                 'verbose',
                 'delete',

                 'graphId',
                 'pendingRows')

    # Maximum number of rows per insert query.
    ROWS_PER_QUERY = 10000

    def __init__(self, modelBase, connection, baseGraph, verbose=False,
                 delete=False):
        self.verbose = verbose
        self.delete = delete

        self.modelBase = modelBase
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.baseGraph = baseGraph

        self._setup()

    def _setup(self):
        # Lookup graph ID
        self.setGraph(self.baseGraph)

        # Create (if it doesn't exist already) a temporary table to
        # hold the results.
        self.cursor.execute("""
            CREATE TEMPORARY TABLE statements_temp1 (
              graph_id integer,
              subject rdf_term,
              predicate rdf_term,
              object rdf_term
            );
            """)

        self.pendingRows = []

    def setGraph(self, graphUri):
        """ Sets the name of the graph to receive triples."""

        # Get graph ID from database
        self.graphId = int(self.modelBase.lookupGraphId(graphUri,
                                                        create=True))

    def triple(self, subject, pred, object):
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

        # Collect the row.
        self.pendingRows.append((self.graphId,
                                 unicode(subject).encode('utf-8'),
                                 unicode(pred).encode('utf-8'),
                                 unicode(object).encode('utf-8'),
                                 isResource, typeUri, lang))

        if len(self.pendingRows) >= self.ROWS_PER_QUERY:
            self._writePendingRows()

    def insertByQuery(self, stmtQuery, stmtsPerRow):
        # Collect needed columns
        columns = ["col_%d" % i for i in range(3*stmtsPerRow)]
        colDecls = ["%s rdf_term" % c for c in columns]

        # Create temporary table to receive the results
        self.cursor.execute("""
            CREATE TEMPORARY TABLE statements_temp_qry (%s) ON COMMIT DROP;
            """ % ','.join(colDecls))

        # Insert data
        self.cursor.execute("INSERT INTO statements_temp_qry (%s);" %
                            stmtQuery)

        # Move data into main data table
        for i in range(stmtsPerRow):
            self.cursor.execute("""
                INSERT INTO
                  statements_temp1 (graph_id, subject, predicate, object)
                SELECT %d, col_%d, col_%d, col_%d
                FROM statements_temp_qry""" % (self.graphId,
                                               i*3+0, i*3+1, i*3+2))

        # Drop intermediate table
        self.cursor.execute("DROP TABLE statements_temp_qry;")

    def _writePendingRows(self):
        if len(self.pendingRows) == 0:
            return

        if self.verbose:
            print "Inserting %d rows..." % (len(self.pendingRows))

        self.cursor.executemany("""
            INSERT INTO statements_temp1 (graph_id, subject, predicate,
                                          object)
            VALUES (
              %d,
              rdf_term(0, %s),
              rdf_term(0, %s),
              rdf_term_create(%s, %d, %s, %s))""",
            self.pendingRows)

        self.pendingRows = []

    def finish(self):
        self._writePendingRows()

        # Delete?
        if self.delete:
            # Remove existing statements.
            if self.verbose:
                print "Removing statements from graph...",
            self.cursor.execute("""
                DELETE FROM graph_statement gs
                USING  statements s, statements_temp1 st
                WHERE s.subject = st.subject AND
                      s.predicate = st.predicate AND
                      s.object = st.object AND
                      gs.stmt_id = s.id AND
                      gs.graph_id = st.graph_id
                """)
            if self.verbose:
                print "%d removed" % self.cursor.rowcount

            # Note: This is a /lot/ more efficient than
            # "... WHERE id NOT IN (SELECT stmt_id FROM statements)"
            if self.verbose:
                print "Removing unused statements..."
            self.cursor.execute("""
                DELETE FROM statements
                USING statements ss LEFT JOIN graph_statement gs
                      ON gs.stmt_id = ss.id
                WHERE gs.stmt_id IS NULL);
                """)
            if self.verbose:
                print "%d removed" % self.cursor.rowcount

        else:
            if self.verbose:
                print "Inserting statements...",
            self.cursor.execute("""
                SELECT insert_statements();
                """)
            if self.verbose:
                print "%s new" % self.cursor.fetchone()[0]

        # Drop statements.
        self.cursor.execute("""
            TRUNCATE TABLE statements_temp1
            """)

    def rollback(self):
        self.connection.rollback()

        self._setup()

    def close(self):
        self.finish()

        self.cursor.close()

        self.connection.commit()
        self.connection.close()

        if self.verbose:
            print "All done!"


_sinkFactories = {
    'singlegraph': SingleGraphRdfSink,
    }

def getSink(modelBase, connection, sinkType, **sinkArgs):
    sinkTypeNorm = sinkType.lower()

    try:
        return _sinkFactories[sinkTypeNorm](modelBase, connection, **sinkArgs)
    except KeyError:
        raise InstantiationError(("Invalid sink type '%s'") % sinkType)
    except TypeError, e:
        raise InstantiationError(("Missing or invalid sink arguments: %s") %
                                 e)
