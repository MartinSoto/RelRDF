from relrdf.error import InstantiationError
from relrdf.expression import uri, literal
from relrdf import commonns

class SingleVersionRdfSink(object):
    """An RDF sink that sends all tuples to a single model version in
    the database."""

    __slots__ = ('connection',
                 'cursor',
                 'versionId',
                 'verbose',

                 'pendingRows')

    # Maximum number of rows per insert query.
    ROWS_PER_QUERY = 10000

    def __init__(self, connection, versionId, verbose=False):
        self.connection = connection
        self.versionId = versionId
        self.verbose = verbose

        self.pendingRows = []

        self.cursor = self.connection.cursor()
        
        self._createTempTable()

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
        
        lang = typeUri = ''
        if isinstance(term, uri.Uri):
            typeUri = commonns.rdfs.Resource
        elif isinstance(term, literal.Literal):
            if not term.typeUri is None:
                typeUri = term.typeUri
            elif not term.lang is None:
                lang = term.lang.lower()
            else:
                typeUri = commonns.rdfs.Literal
        else:
            assert False, "Unexpected object type '%d'" \
                   % object.__class__.__name__

        val = unicode(term).encode('utf-8')
        typeUri = unicode(typeUri).encode('utf-8')
        lang = unicode(lang).encode('utf-8')

        return (val, typeUri, lang)

    def triple(self, subject, pred, object):
        
        self.pendingRows.append(self._prepareForDB(subject) + 
                                self._prepareForDB(pred) + 
                                self._prepareForDB(object))
        
        if len(self.pendingRows) >= self.ROWS_PER_QUERY:
            self._writePendingRows()
                                
    def _writePendingRows(self):
        if len(self.pendingRows) == 0:
            return

        if self.verbose:
            print "Inserting %d rows..." % (len(self.pendingRows))

        self.cursor.executemany(
            """
            INSERT INTO statements_temp1 VALUES (
              rdf_term_create(%s, %s, %s),
              rdf_term_create(%s, %s, %s),
              rdf_term_create(%s, %s, %s))""",
            self.pendingRows)
        
        self.pendingRows = []

    def finish(self):
        self._writePendingRows()
        
        # Write RDF term values
        writeFormat = 2;
        
        # Create temporary table to hold statement IDs
        self.cursor.execute(
            """
            CREATE TEMPORARY TABLE version_statement_temp1 (
                version_id integer,
                stmt_id integer
            ) ON COMMIT DROP;
            """)
                
        existIDs = []

        # Get IDs of existing statements
        if self.verbose:
            print "Checking for existing statements..."
        self.cursor.execute(
            """
            INSERT INTO version_statement_temp1 (version_id, stmt_id)
              SELECT %d, ss.id
                FROM statements_temp1 s
                  RIGHT JOIN statements ss
                      ON ss.subject = s.subject AND
                         ss.predicate = s.predicate AND
                         ss.object = s.object
            """ % int(self.versionId)) 
        
        # Insert the statements into the statements table.
        # Note: The rdf_term_create constructor used in the creation of
        #       the statements_temp2 above might fail leading to
        #       NULL values to appear. These are filtered out here.
        #       Maybe we might want to raise an error here? The
        #       DAWG test cases seem to expect us to keep going, so
        #       that's what we do...
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
        ids = [(int(self.versionId), x.pop()) for x in ids]
        self.cursor.executemany(
            """
            INSERT INTO version_statement_temp1 (version_id, stmt_id)
                VALUES (%d, %d)
            """, ids)
        
        # Add the statement numbers to the version.
        if self.verbose:
            print "Saving version information..."        
        self.cursor.execute(
            """
            INSERT INTO version_statement (version_id, stmt_id)
                SELECT vt.version_id, vt.stmt_id
                  FROM version_statement_temp1 vt
                    LEFT JOIN version_statement v ON v.version_id = vt.version_id AND v.stmt_id = vt.stmt_id
                WHERE v.stmt_id IS NULL
            """)
        
        # Drop temporary table contents
        self.cursor.execute(
            """
            DELETE FROM statements_temp1
            """)
        self.cursor.execute(
            """
            DROP TABLE version_statement_temp1
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
    'singleversion': SingleVersionRdfSink,
    }

def getSink(connection, sinkType, **sinkArgs):
    sinkTypeNorm = sinkType.lower()

    try:
        return _sinkFactories[sinkTypeNorm](connection, **sinkArgs)
    except KeyError:
        raise InstantiationError(_("Invalid sink type '%s'") % sinkType)
    except TypeError, e:
        raise InstantiationError(_("Missing or invalid sink arguments: %s") %
                                 e)
