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

        # FIXME: A bug/limitation in MySQL causes an automatic commit
        # whenever a table is dropped. To work around it, we use a
        # different table for each required width and reuse them as
        # needed. See basicquery.SingleVersionMapper.

        # Create (if it doesn't exist already) a temporary table to
        # hold the results. We create the hash column but don't fill
        # it, since method 'close' issues an update to do this at
        # server side.
        self.cursor.execute(
            """
            CREATE TEMPORARY TABLE statements_temp1 (
              subject_text text NOT NULL,
              predicate_text text NOT NULL,
              object_type text NOT NULL,
              object_text text NOT NULL
            ) ON COMMIT DROP;
            """)
        
    def triple(self, subject, pred, object):
        if isinstance(object, uri.Uri):
            objectType = commonns.rdfs.Resource
        elif isinstance(object, literal.Literal):
            if object.typeUri is None:
                objectType = commonns.rdfs.Literal
            else:
                objectType = object.typeUri
        else:
            assert False, "Unexpected object type '%d'" \
                   % object.__class__.__name__

        self.pendingRows.append((unicode(subject).encode('utf-8'),
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
              (subject_text, predicate_text, object_type, object_text)
            VALUES (%s, %s, %s, %s)""",
            self.pendingRows)
        
        self.pendingRows = []

    def finish(self):
        self._writePendingRows()
        
        writeNum = False;
        
        # Create any missing data types.
        if self.verbose:
            print "Creating data types..."
        self.cursor.execute(
            """
            INSERT INTO data_types (uri)              
              SELECT DISTINCT s.object_type
              FROM statements_temp1 s LEFT JOIN data_types dt 
                  ON s.object_type = dt.uri
              WHERE dt.id IS NULL
            """)        
       
        self.cursor.execute(
            """
            CREATE TEMPORARY TABLE version_statement_temp1 (
                version_id integer,
                stmt_id integer
            ) ON COMMIT DROP;
            """)
                
        existIDs = []
        if writeNum:
            
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
            
            
        else:
            
            # Get IDs of existing statements
            if self.verbose:
                print "Checking for existing statements..."
            self.cursor.execute(
                """
                INSERT INTO version_statement_temp1 (version_id, stmt_id)
                    SELECT %d, ss.id FROM statements_temp1 s
                      RIGHT JOIN statements ss ON s.subject_text = ss.subject_text AND s.predicate_text = ss.predicate_text AND s.object_text = ss.object_text
                """ % int(self.versionId)) 
            
            # Insert the statements into the statements table.
            if self.verbose:
                print "Inserting statements..."
            self.cursor.execute(
                """
                INSERT INTO statements (subject_text, predicate_text, object_type,
                                        object_text)
                 SELECT DISTINCT s.subject_text, s.predicate_text, dt.id, s.object_text
                  FROM statements_temp1 s
                      LEFT JOIN data_types dt ON s.object_type = dt.uri
                      LEFT JOIN statements ss
                          ON ss.subject_text = s.subject_text AND
                             ss.predicate_text = s.predicate_text AND
                             ss.object_text = s.object_text
                  WHERE ss.id IS NULL
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
        
        self.cursor.execute(
            """
            CREATE TEMPORARY TABLE statements_temp1 (
              subject_text text NOT NULL,
              predicate_text text NOT NULL,
              object_type text NOT NULL,
              object_text text NOT NULL
            ) ON COMMIT DROP;
            """)
                
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
