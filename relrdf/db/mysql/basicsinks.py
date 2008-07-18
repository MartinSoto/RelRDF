from relrdf.error import InstantiationError
from relrdf.expression import uri, blanknode, literal


class SingleVersionRdfSink(object):
    """An RDF sink that sends all tuples to a single model version in
    the database."""

    __slots__ = ('connection',
                 'cursor',
                 'versionId',

                 'pendingRows')

    # Maximum number of rows per insert query.
    ROWS_PER_QUERY = 100

    def __init__(self, connection, versionId):
        self.connection = connection
        self.versionId = versionId

        self.pendingRows = []

        self.cursor = self.connection.cursor()

        # Create (if it doesn't exist already) a temporary table to
        # hold the results. We create the hash column but don't fill
        # it, since method 'close' issues an update to do this at
        # server side.
        self.cursor.execute(
            """
            CREATE TEMPORARY TABLE IF NOT EXISTS statements_temp_sink (
              hash binary(16),
              subject_text longtext NOT NULL,
              predicate_text longtext NOT NULL,
              object_type longtext NOT NULL,
              object_text longtext NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8
            COMMENT='Available statements';
            """)

        # Clean up the table contents in case the table was already
        # there.
        self.cursor.execute(
            """
            DELETE FROM statements_temp_sink;
            """)

    def triple(self, subject, pred, object):
        if isinstance(object, uri.Uri):
            objectType = '<RESOURCE>'
        elif isinstance(object, blanknode.BlankNode):
            objectType = '<BLANKNODE>'
        elif isinstance(object, literal.Literal):
            if object.typeUri is None:
                objectType = '<LITERAL>'
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

        self.cursor.executemany(
            """
            INSERT INTO statements_temp_sink
              (subject_text, predicate_text, object_type, object_text)
            VALUES (_utf8%s, _utf8%s, _utf8%s, _utf8%s)""",
            self.pendingRows)

        self.pendingRows = []

    def close(self):
        self._writePendingRows()

        # Update the hash values.
        self.cursor.execute(
            """
            UPDATE statements_temp_sink
              SET hash = unhex(md5(concat(subject_text, predicate_text,
                                          object_text)));
            """)

        # Create any missing data types.
        self.cursor.execute(
            """
            INSERT INTO data_types (uri)
              SELECT s.object_type
              FROM statements_temp_sink s
            ON DUPLICATE KEY UPDATE uri = uri;
            """)

        # Insert the statements into the statements table.
        self.cursor.execute(
            """
            INSERT INTO statements (hash, subject, predicate, object,
                                    subject_text, predicate_text, object_type,
                                    object_text)
              SELECT s.hash, unhex(md5(subject_text)),
                     unhex(md5(predicate_text)),
                     unhex(md5(object_text)), s.subject_text, s.predicate_text,
                     dt.id, s.object_text
              FROM statements_temp_sink s, data_types dt
              WHERE s.object_type = dt.uri
            ON DUPLICATE KEY UPDATE statements.subject = statements.subject;
            """)

        # Add the statement numbers to the version.
        self.cursor.execute(
            """
            INSERT INTO version_statement (version_id, stmt_id)
              SELECT %d AS v_id, s.id
              FROM statements s, statements_temp_sink st
              WHERE s.hash = st.hash
            ON DUPLICATE KEY UPDATE version_id = version_id;
            """ % int(self.versionId))

        # Clean up the table contents, but don't drop it, since a drop
        # forces a commit.
        self.cursor.execute(
            """
            DELETE FROM statements_temp_sink;
            """)

        self.cursor.close()

        self.connection.commit()
        self.connection.close()


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
