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
    """An RDF sink that sends all tuples to a single graph in the database."""

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

    def __init__(self, modelBase, connection, baseGraph, verbose=False, delete=False):
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
        self.cursor.execute(
            """
            CREATE TEMPORARY TABLE statements_temp1 (
              subject rdf_term,
              predicate rdf_term,
              object rdf_term
            ) ON COMMIT DROP;
            """)
        
        self.pendingRows = []

    def setGraph(self, graphUri):
        """ Sets the name of the graph to receive triples."""
        
        # Get graph ID from database
        self.graphId = self.modelBase.lookupGraphId(graphUri, 
                                                    connection=self.connection,
                                                    create=True)

        
    def _prepareForDB(self, term):
        """Returns argument triple to pass to the rdf_term_create
           function to create the appropriate term"""
        
        lang = typeUri = None
        isResource = 0
        if isinstance(term, uri.Uri):
            isResource = 1
        elif isinstance(term, literal.Literal):
            if not term.typeUri is None:
                typeUri = unicode(term.typeUri).encode('utf-8')
            elif not term.lang is None:
                lang = unicode(term.lang.lower()).encode('utf-8')
        else:
            assert False, "Unexpected object type '%d'" \
                   % object.__class__.__name__

        val = unicode(term).encode('utf-8')

        return (val, isResource, typeUri, lang)

    def triple(self, subject, pred, object):
        
        self.pendingRows.append(self._prepareForDB(subject) + 
                                self._prepareForDB(pred) + 
                                self._prepareForDB(object))
        
        if len(self.pendingRows) >= self.ROWS_PER_QUERY:
            self._writePendingRows()
            
    def insertByQuery(self, stmtQuery, stmtsPerRow):

        # Collect needed columns
        columns = ["col_%d" % i for i in range(3*stmtsPerRow)]
        colDecls = ["%s rdf_term" % c for c in columns]
        
        # Create temporary table to receive the results
        self.cursor.execute(
            """
            CREATE TEMPORARY TABLE statements_temp_qry (%s) ON COMMIT DROP;
            """ % ','.join(colDecls))
        
        # Insert data
        self.cursor.execute("INSERT INTO statements_temp_qry (%s);" % stmtQuery)  
            
        # Move data into main data table
        for i in range(stmtsPerRow):
            self.cursor.execute(
                """
                INSERT INTO statements_temp1 SELECT col_%s, col_%s, col_%s FROM statements_temp_qry;
                """ % (i*3+0, i*3+1, i*3+2))
        
        # Drop intermediate table
        self.cursor.execute("DROP TABLE statements_temp_qry;")
        
                                
    def _writePendingRows(self):
        if len(self.pendingRows) == 0:
            return

        if self.verbose:
            print "Inserting %d rows..." % (len(self.pendingRows))

        self.cursor.executemany(
            """
            INSERT INTO statements_temp1 (subject, predicate, object) VALUES (
              rdf_term_create(%s, %d, %s, %s),
              rdf_term_create(%s, %d, %s, %s),
              rdf_term_create(%s, %d, %s, %s))""",
            self.pendingRows)
        
        self.pendingRows = []

    def finish(self):
        self._writePendingRows()
      
        # Delete?
        if self.delete:
            
            # Drop statements (not needed anymore)
            self.cursor.execute(
                """
                TRUNCATE TABLE statements_temp1
                """)            
            
            # Remove existing statements
            if self.verbose:
                print "Removing statements from graph...",   
            self.cursor.execute(
                """
                DELETE FROM graph_statement vs
                  WHERE graph_id = %d AND stmt_id IN 
                    (SELECT stmt_id FROM graph_statement_temp1)
                """ % int(self.graphId))
            if self.verbose:
                print "%d removed" % self.cursor.rowcount             

            # Note: This is a /lot/ more efficient than
            # "... WHERE id NOT IN (SELECT stmt_id FROM statements)"
            if self.verbose:
                print "Removing unused statements..."
            self.cursor.execute(
                """
                DELETE FROM statements WHERE id IN
                  (SELECT ss.id FROM statements ss
                                LEFT JOIN graph_statement gs
                                ON gs.stmt_id = ss.id
                   WHERE gs.stmt_id IS NULL);
                """)
            if self.verbose:
                print "%d removed" % self.cursor.rowcount
                
        else:
            if self.verbose:
                print "Inserting statements...",  
            self.cursor.execute(
                """
                SELECT insert_statements(%d);
                """ % int(self.graphId))
            if self.verbose:
                print "%s new" % self.cursor.fetchone()[0]
        
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
