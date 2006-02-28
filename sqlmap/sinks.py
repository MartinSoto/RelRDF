from expression import uri, blanknode, literal


class VersionRdfSink(object):
    """An RDF sink that sends all tuples to a single model version in
    the database."""

    __slots__ = ('cursor',
                 'versionId')

    def __init__(self, cursor, versionId):
        self.cursor = cursor
        self.versionId = versionId

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
            
        self.cursor.execute(
            """
            INSERT INTO data_types (uri)
            VALUES (%s)
            ON DUPLICATE KEY UPDATE uri = uri""",
            (unicode(objectType)))
        self.cursor.execute(
            """
            INSERT INTO statements (subject, predicate, object_type, object)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE subject = subject""",
            (unicode(subject), unicode(pred), self.cursor.lastrowid,
             unicode(object)))
        self.cursor.execute(
            """
            INSERT INTO version_statement (version_id, stmt_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE version_id = version_id""",
            (self.versionId, self.cursor.lastrowid))
