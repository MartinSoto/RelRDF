from relrdf.error import InstantiationError
from relrdf.expression import uri, literal
from relrdf import commonns

class SingleGraphRdfSink(object):
    """An RDF sink that sends all tuples to a single graph in the database."""

    __slots__ = ('connection',
                 'cursor',
                 'graphId',
                 'verbose',
                 'delete',

                 'pendingRows',
                 'rowsAffected')

    # Maximum number of rows per insert query.
    ROWS_PER_QUERY = 10000

    def __init__(self, connection, graphUri, verbose=False, delete=False):
        self.connection = connection
        self.verbose = verbose
        self.delete = delete

        self.pendingRows = []
        self.rowsAffected = 0

        self.cursor = self.connection.cursor()
        
        # Get graph ID
        self.graphId = self._lookupGraphUri(graphUri)
        
        self._createTempTable()
        
    def _lookupGraphUri(self, graphUri):
        
        graphUri = unicode(graphUri).encode('utf-8')
        
        # Try lookup
        self.cursor.execute("""SELECT graph_id FROM graphs WHERE graph_uri = '%s';""" % graphUri)        
        result = self.cursor.fetchone()
        if not result is None:
            return result[0]
        
        # Insert new graph
        self.cursor.execute("INSERT INTO graphs (graph_uri) VALUES ('%s') RETURNING graph_id;" % graphUri)
        result = self.cursor.fetchone()
        assert not result is None, "Could not create a new graph!"

        # Done
        return result[0]

    def _createTempTable(self):
        
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
            INSERT INTO statements_temp1 VALUES (
              rdf_term_create(%s, %d, %s, %s),
              rdf_term_create(%s, %d, %s, %s),
              rdf_term_create(%s, %d, %s, %s))""",
            self.pendingRows)
        
        self.pendingRows = []

    def finish(self):
        self._writePendingRows()
        
        # Create temporary table to hold statement IDs
        self.cursor.execute(
            """
            CREATE TEMPORARY TABLE graph_statement_temp1 (
                graph_id integer,
                stmt_id integer
            ) ON COMMIT DROP;
            """)
                
        existIDs = []

        # Get IDs of existing statements
        if self.verbose:
            print "Checking for existing statements..."
        self.cursor.execute(
            """
            INSERT INTO graph_statement_temp1 (graph_id, stmt_id)
              SELECT %d, ss.id
                FROM statements_temp1 s
                  LEFT JOIN statements ss
                      ON ss.subject = s.subject AND
                         ss.predicate = s.predicate AND
                         ss.object = s.object
            """ % int(self.graphId)) 
        
        # Delete?
        if self.delete:
            
            if self.verbose:
                print "Removing statements from graph..."
            
            self.cursor.execute(
                """
                DELETE FROM graph_statement vs
                  WHERE graph_id = %d AND stmt_id IN 
                    (SELECT stmt_id FROM graph_statement_temp1)
                """ % int(self.graphId))
            
            if self.verbose:
                print "Removing unused statements..."
            self.cursor.execute(
                """
                DELETE FROM statements ss
                  WHERE NOT id IN (SELECT stmt_id FROM graph_statement)
                """)            
                
        else:
            
            # Insert the statements into the statements table.
            # Note: The rdf_term_create constructor used in the creation of
            #       the statements_temp2 above might fail leading to
            #       NULL values to appear. These are filtered out here.
            #       Maybe we might want to raise an error here? The
            #       DAWG test cases seem to expect us to keep going, so
            #       that's what we do...
            # Note 2: Seems what the DAWG test cases actually want us
            #         to accept invalid terms into the data base.
            #         The rules to use for these terms aren't properly
            #         defined though, so we leave it like this for now.
            if self.verbose:
                print "Inserting statements..."
            self.cursor.execute(
                """
                INSERT INTO statements (subject, predicate, object)
                  SELECT DISTINCT s.subject, s.predicate, s.object
                    FROM statements_temp1 s
                      LEFT JOIN statements ss
                          ON ss.subject = s.subject AND
                             ss.predicate = s.predicate AND
                             ss.object = s.object
                    WHERE ss.id IS NULL
                      AND s.subject IS NOT NULL
                      AND s.predicate IS NOT NULL
                      AND s.object IS NOT NULL                      
                  RETURNING id
                """)
                        
            # Get IDs of newly inserted rows
            ids = self.cursor.fetchall()
            ids = [(int(self.graphId), x.pop()) for x in ids]
            self.cursor.executemany(
                """
                INSERT INTO graph_statement_temp1 (graph_id, stmt_id)
                    VALUES (%d, %d)
                """, ids)
            
            # Add the statement numbers to the graph.
            if self.verbose:
                print "Saving graph information..."        
            self.cursor.execute(
                """
                INSERT INTO graph_statement (graph_id, stmt_id)
                    SELECT vt.graph_id, vt.stmt_id
                      FROM graph_statement_temp1 vt
                        LEFT JOIN graph_statement v ON v.graph_id = vt.graph_id AND v.stmt_id = vt.stmt_id
                    WHERE v.stmt_id IS NULL
                """)
            
        # Query row count
        self.cursor.execute("SELECT COUNT(*) FROM statements_temp1")
        count = self.cursor.fetchone()[0]
        self.rowsAffected += count
        
        # Drop temporary table contents
        self.cursor.execute(
            """
            DELETE FROM statements_temp1
            """)
        self.cursor.execute(
            """
            DROP TABLE graph_statement_temp1
            """)
        
    def rollback(self):
        
        self.connection.rollback()
        
        self._createTempTable()
                
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

def getSink(connection, sinkType, **sinkArgs):
    sinkTypeNorm = sinkType.lower()

    try:
        return _sinkFactories[sinkTypeNorm](connection, **sinkArgs)
    except KeyError:
        raise InstantiationError(("Invalid sink type '%s'") % sinkType)
    except TypeError, e:
        raise InstantiationError(("Missing or invalid sink arguments: %s") %
                                 e)
