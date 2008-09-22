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
              subject_type text NOT NULL,
              subject_text text NOT NULL,
              predicate_type text NOT NULL,
              predicate_text text NOT NULL,
              object_type text NOT NULL,
              object_text text NOT NULL
            ) ON COMMIT DROP;
            """)
        
    def _typeUri(self, term):
        
        if isinstance(term, uri.Uri):
            return commonns.rdfs.Resource
        elif isinstance(term, literal.Literal):
            if term.typeUri is None:
                return commonns.rdfs.Literal
            else:
                return term.typeUri
        else:
            assert False, "Unexpected object type '%d'" \
                   % object.__class__.__name__
        

    def triple(self, subject, pred, object):
        
        subjectType = self._typeUri(subject)
        predType = self._typeUri(pred)
        objectType = self._typeUri(object)

        self.pendingRows.append((unicode(subjectType).encode('utf-8'),
                                 unicode(subject).encode('utf-8'),
                                 unicode(predType).encode('utf-8'),
                                 unicode(pred).encode('utf-8'),
                                 unicode(objectType).encode('utf-8'),
                                 unicode(object).encode('utf-8')))
        if len(self.pendingRows) >= self.ROWS_PER_QUERY:
            self._writePendingRows()
                                
    def _writePendingRows(self):
        if len(self.pendingRows) == 0:
            return

        if self.verbose:
            print "Inserting %d rows..." % (len(self.pendingRows))

        self.cursor.executemany(
            """
            INSERT INTO statements_temp1
              (subject_type, subject_text, predicate_type, predicate_text, object_type, object_text)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            self.pendingRows)
        
        self.pendingRows = []

    def finish(self):
        self._writePendingRows()
        
        # Write RDF term values
        writeFormat = 2;
        
        # Create any missing data types.
        if self.verbose:
            print "Creating data types..."
        for typeColumn in ("subject_type", "predicate_type", "object_type"):
            self.cursor.execute(
                """
                INSERT INTO data_types (uri)              
                  SELECT DISTINCT s.%s
                  FROM statements_temp1 s LEFT JOIN data_types dt 
                      ON s.%s = dt.uri
                  WHERE dt.id IS NULL
                """ % (typeColumn, typeColumn))
            
        # Create temporary table to hold statement IDs
        self.cursor.execute(
            """
            CREATE TEMPORARY TABLE version_statement_temp1 (
                version_id integer,
                stmt_id integer
            ) ON COMMIT DROP;
            """)
                
        existIDs = []
        if writeFormat == 0:
            
            # Create any missing text values
            if self.verbose:
                print "Registering subject texts..."
            self.cursor.execute(
                """
                INSERT INTO statement_text (txt)
                  SELECT DISTINCT s.subject_text
                  FROM statements_temp1 s 
                       LEFT JOIN statement_text t ON s.subject_text = t.txt
                  WHERE t.id IS NULL
                """)
            if self.verbose:
                print "Registering predicate texts..."
            self.cursor.execute(
                """
                INSERT INTO statement_text (txt)
                  SELECT DISTINCT s.predicate_text
                  FROM statements_temp1 s 
                       LEFT JOIN statement_text t ON s.predicate_text = t.txt
                  WHERE t.id IS NULL
                """)
            if self.verbose:
                print "Registering object texts..."
            self.cursor.execute(
                """
                INSERT INTO statement_text (txt)
                  SELECT DISTINCT substr(s.object_text, 0, 2700)
                  FROM statements_temp1 s
                       LEFT JOIN statement_text t ON substr(s.object_text, 0, 2700) = t.txt
                  WHERE t.id IS NULL
                """)
            
            # Get IDs of existing statements
            if self.verbose:
                print "Checking for existing statements..."
            self.cursor.execute(
                """
                INSERT INTO version_statement_temp1
                    SELECT %d, ss.id FROM statements_temp1 s
                      LEFT JOIN statement_text st ON s.subject_text = st.txt
                      LEFT JOIN statement_text pt ON s.predicate_text = pt.txt
                      LEFT JOIN statement_text ot ON substr(s.object_text, 0, 2700) = ot.txt
                      RIGHT JOIN statements ss ON ss.subject = st.id AND ss.predicate = pt.id AND ss.object = ot.id
                """ % int(self.versionId))
            
            # Insert the statements into the statements table.
            if self.verbose:
                print "Inserting new statements..."
            self.cursor.execute(
                """
                INSERT INTO statements (subject, predicate, object_type,
                                        object)
                 SELECT DISTINCT st.id, pt.id, dt.id, ot.id
                  FROM statements_temp1 s
                      LEFT JOIN statement_text st ON s.subject_text = st.txt
                      LEFT JOIN statement_text pt ON s.predicate_text = pt.txt
                      LEFT JOIN data_types dt ON s.object_type = dt.uri
                      LEFT JOIN statement_text ot ON substr(s.object_text, 0, 2700) = ot.txt
                      LEFT JOIN statements ss ON ss.subject = st.id AND ss.predicate = pt.id AND ss.object = ot.id
                  WHERE ss.id IS NULL
                  RETURNING id
                """)
            
            
        elif writeFormat == 1:
            
            pass
            
        else:
            
            # Convert statements to RDF term objects (look up data type IDs)
            if self.verbose:
                print "Converting to RDF terms..."            
            self.cursor.execute(
                """
                CREATE TEMPORARY TABLE statements_temp2 (subject, predicate, object)
                  ON COMMIT DROP
                  AS SELECT
                       rdf_term(st.id, s.subject_text),
                       rdf_term(pt.id, s.predicate_text),
                       rdf_term(ot.id, s.object_text) 
                     FROM statements_temp1 s
                       LEFT JOIN data_types st ON s.subject_type = st.uri
                       LEFT JOIN data_types pt ON s.predicate_type = pt.uri
                       LEFT JOIN data_types ot ON s.object_type = ot.uri                       
                """)
            
            # Get IDs of existing statements
            if self.verbose:
                print "Checking for existing statements..."
            self.cursor.execute(
                """
                INSERT INTO version_statement_temp1 (version_id, stmt_id)
                  SELECT %d, ss.id
                    FROM statements_temp2 s
                      RIGHT JOIN statements ss
                          ON ss.subject = s.subject AND
                             ss.predicate = s.predicate AND
                             ss.object = s.object
                """ % int(self.versionId)) 
            
            # Insert the statements into the statements table.
            # Note: The rdf_term constructor used in the creation of
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
                    FROM statements_temp2 s
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
