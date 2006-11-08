import md5

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

        self.cursor.execute(
            """
            DROP TABLE IF EXISTS statements_temp;
            """)

        self.cursor.execute(
            """
            CREATE TEMPORARY TABLE statements_temp (
              hash binary(16) NOT NULL,
              subject varchar(255) NOT NULL,
              predicate varchar(255) NOT NULL,
              object_type varchar(255) NOT NULL,
              object longtext NOT NULL
            ) ENGINE=MyISAM DEFAULT CHARSET=utf8
            COMMENT='Available statements';
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

        # Calculate a hash value for the statement.
        m = md5.new()
        m.update(subject.encode('utf-8'))
        m.update(pred.encode('utf-8'))
        m.update(objectType.encode('utf-8'))
        m.update(unicode(object).encode('utf-8'))

        self.pendingRows.append((m.digest(),
                                 unicode(subject).encode('utf-8'),
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
            INSERT INTO statements_temp
              (hash, subject, predicate, object_type, object)
            VALUES (_binary%s,_utf8%s,_utf8%s,_utf8%s,_utf8%s)""",
            self.pendingRows)

        self.pendingRows = []

    def close(self):
        self._writePendingRows()

        self.cursor.execute(
            """
            CALL insert_version(%s)
            """, self.versionId)

        self.cursor.close()


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
