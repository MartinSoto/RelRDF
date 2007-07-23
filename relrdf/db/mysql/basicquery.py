from relrdf.error import InstantiationError
from relrdf import mapping, parserfactory, commonns

from relrdf.typecheck import dynamic
from relrdf.expression import uri, blanknode, literal, nodes, build
from relrdf.mapping import transform, valueref, sqlnodes, emit

from relrdf.typecheck.typeexpr import LiteralType, BlankNodeType, \
     ResourceType, RdfNodeType, resourceType, rdfNodeType


TYPE_ID_RESOURCE = literal.Literal(1)
TYPE_ID_BLANKNODE = literal.Literal(2)
TYPE_ID_LITERAL = literal.Literal(3)


class UriValueMapping(valueref.ValueMapping):
    """A value mapping capable of converting from arbitrary internal
    values to an external representation formed by prepending a base
    URI to the canonical string representation of the internal value."""

    __slots__ = ('baseUri',
                 'intToExtExpr',
                 'extToIntExpr')

    def __init__(self, baseUri):
        super(UriValueMapping, self).__init__()

        self.baseUri = baseUri

        self.intToExtExpr = 'CONCAT("%s", $0$)' % baseUri

        l = len(baseUri.encode('utf-8'))
        self.extToIntExpr = '''
        IF(SUBSTRING($0$, 1, %d) = "%s",
           SUBSTRING($0$, %d), "<<<NO VALUE>>>")''' % (l, baseUri, l + 1)

    def intToExt(self, internal):
        return sqlnodes.SqlScalarExpr(self.intToExtExpr, internal)

    def extToInt(self, expr):
        return sqlnodes.SqlScalarExpr(self.extToIntExpr, expr)


def uriValueRef(incarnation, fieldId, mapping):
    return valueref.ValueRef(mapping.copy(),
                             sqlnodes.SqlFieldRef(incarnation, fieldId))


class ChecksumValueMapping(valueref.ValueMapping):
    """A value mapping that uses a checksum column as internal
    representation, and a parallel text column as external
    representation. The checksum column is expected to contain a
    robust checksum (i.e., MD5) of the corresponding text value, so
    that it is possible to compare checksums instead of values, and
    still have a very low probability of false possitives.

    The internal expression must be a field reference pointing to the
    checksum field. The corresponding text field must be named by
    appending '_text' to the name of the checksum field."""

    __slots__ = ()

    def intToExt(self, internal):
        assert isinstance(internal, sqlnodes.SqlFieldRef)
        return sqlnodes.SqlFieldRef(internal.incarnation,
                                    internal.fieldId + '_text')

    def extToInt(self, expr):
        return sqlnodes.SqlScalarExpr('unhex(md5(convert($0$ using utf8)))',
                                      expr)


def checksumValueRef(incarnation, fieldId):
    return valueref.ValueRef(ChecksumValueMapping(),
                             sqlnodes.SqlFieldRef(incarnation, fieldId))


class BasicMapper(transform.PureRelationalTransformer):
    """A base mapper for the MySQL basic schema. It handles the
    mapping of type expressions."""

    def prepareConnection(self, connection):
        """Prepares the database connection (i.e., by creating certain
        temporary tables) for use with this mapping."""
        pass

    def releaseConnection(self, connection):
        """Releases from the connection any resources created by
        `prepareConnection` method."""
        pass

    def mapTypeExpr(self, typeExpr):
        if isinstance(typeExpr, LiteralType):
            # FIXME:Search for the actual type id.
            return nodes.Literal(TYPE_ID_LITERAL)
        elif isinstance(typeExpr, BlankNodeType):
            return nodes.Literal(TYPE_ID_BLANKNODE)
        elif isinstance(typeExpr, ResourceType):
            return nodes.Literal(TYPE_ID_RESOURCE)
        else:
            assert False, "Cannot determine type"


class BasicSingleVersionMapper(BasicMapper):
    """Abstract class that targets an abstract query to a context set
    with only one element corresponding to a single version of a
    model. Reified patterns are not handled at all."""
    
    __slots__ = ('versionId',
                 'versionUri',

                 'versionMapping',
                 'stmtRepl')

    def __init__(self, versionId, versionUri):
        super(BasicSingleVersionMapper, self).__init__()

        self.versionId = int(versionId)
        self.versionUri = versionUri

        self.versionMapping = UriValueMapping(versionUri)

        # Cache for the statement pattern replacement expression.
        self.stmtRepl = None

    def replStatementPattern(self, expr):
        if self.stmtRepl is not None:
            return self.stmtRepl

        rel = build.buildExpression(
            (nodes.Select,
             (nodes.Product,
              (sqlnodes.SqlRelation, 1, 'version_statement'),
              (sqlnodes.SqlRelation, 2, 'statements')),
             (nodes.And,
              (nodes.Equal,
               (sqlnodes.SqlFieldRef, 1, 'version_id'),
               (nodes.Literal, self.versionId)),
              (nodes.Equal,
               (sqlnodes.SqlFieldRef, 1, 'stmt_id'),
               (sqlnodes.SqlFieldRef, 2, 'id'))))
            )

        replExpr = \
          nodes.MapResult(['context', 'type__context',
                           'subject', 'type__subject',
                           'predicate', 'type__predicate',
                           'object', 'type__object'],
                          rel,
                          nodes.Uri(self.versionUri + str(self.versionId)),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          checksumValueRef(2, 'subject'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          checksumValueRef(2, 'predicate'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          checksumValueRef(2, 'object'),
                          sqlnodes.SqlFieldRef(2, 'object_type'))

        self.stmtRepl = (replExpr,
                         ('context', 'subject', 'predicate', 'object'))

        return self.stmtRepl


class SingleVersionMapper(BasicSingleVersionMapper,
                          transform.StandardReifTransformer):
    """Targets an abstract query to a context set with only one
    element corresponding to a single version of a model. Reified
    patterns are interpreted as four normal patterns in the standard
    RDFS fashion."""

    __slots__ = ()

    name = "Single Version"
    parameterInfo = ({"name":"versionId", "label":"Version ID", "tip":"Enter the ID of the version to be used", "assert":"versionId != ''", "asserterror":"Version ID must not be empty"},)

    def __init__(self, versionId, versionUri=commonns.relrdf.version):
        super(SingleVersionMapper, self).__init__(versionId,
                                                  versionUri)


class AllVersionsMapper(BasicMapper,
                        transform.StandardReifTransformer):
    """Targets an abstract query to a context set whose elements are
    the versions of a model."""
    
    __slots__ = ('versionMapping',

                 'stmtRepl')
    name = "All Versions"
    parameterInfo = ()

    def __init__(self, versionUri=commonns.relrdf.version,
                 stmtUri=commonns.relrdf.stmt, metaInfoVersion=1):
        super(AllVersionsMapper, self).__init__()

        self.versionMapping = UriValueMapping(versionUri)

        # Cache for the statement pattern replacement expression.
        self.stmtRepl = None

    def replStatementPattern(self, expr):
        if self.stmtRepl is not None:
            return self.stmtRepl

        rel = build.buildExpression(
            (nodes.Select,
             (nodes.Product,
              (sqlnodes.SqlRelation, 1, 'version_statement'),
              (sqlnodes.SqlRelation, 2, 'statements')),
             (nodes.Equal,
              (sqlnodes.SqlFieldRef, 1, 'stmt_id'),
              (sqlnodes.SqlFieldRef, 2, 'id')))
            )

        replExpr = \
          nodes.MapResult(['context', 'type__context',
                           'subject', 'type__subject',
                           'predicate', 'type__predicate',
                           'object', 'type__object'],
                          rel,
                          uriValueRef(1, 'version_id', self.versionMapping),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          checksumValueRef(2, 'subject'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          checksumValueRef(2, 'predicate'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          checksumValueRef(2, 'object'),
                          sqlnodes.SqlFieldRef(2, 'object_type'))

        self.stmtRepl = (replExpr,
                         ('context', 'subject', 'predicate', 'object'))

        return self.stmtRepl


class MetaVersionMapper(BasicSingleVersionMapper,
                        transform.MatchReifTransformer):
    """Targets an abstract query to a context with only one element
    corresponding to version 1 of a model (the meta-information
    version). Reified patterns will match statements present in all
    model versions. A special relation relrdf:versionContainsStmt can
    be used to determine which statements are in which version."""

    __slots__ = ('stmtUri',

                 'stmtMapping',
                 'reifStmtRepl')
                 
    name = "Meta Version"
    parameterInfo = ()

    def __init__(self, versionUri=commonns.relrdf.version,
                 stmtUri=commonns.relrdf.stmt):
        super(MetaVersionMapper, self).__init__(1, versionUri)

        self.stmtUri = stmtUri

        self.stmtMapping = UriValueMapping(stmtUri)

        # Cache for the reified statement pattern replacement expression.
        self.reifStmtRepl = None

    def replStatementPattern(self, expr):
        replExpr = None

        if isinstance(expr[2], nodes.Uri) and \
           expr[2].uri == commonns.rdf.type and \
           isinstance(expr[3], nodes.Uri) and \
           expr[3].uri == commonns.rdf.Statement:
            rel = sqlnodes.SqlRelation(1, 'statements')
            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              nodes.Uri(self.versionUri + '1'),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              uriValueRef(1, 'id', self.stmtMapping),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              nodes.Literal(commonns.rdf.type),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              nodes.Literal(commonns.rdf.Statement),
                              nodes.Literal(TYPE_ID_RESOURCE))
        elif isinstance(expr[2], nodes.Uri) and \
             expr[2].uri == commonns.relrdf.versionContainsStmt:
            rel = sqlnodes.SqlRelation(1, 'version_statement')
            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              nodes.Uri(self.versionUri + '1'),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              uriValueRef(1, 'version_id',
                                          self.versionMapping),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              nodes.Literal(commonns.relrdf. \
                                            versionContainsStmt),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              uriValueRef(1, 'stmt_id', self.stmtMapping),
                              nodes.Literal(TYPE_ID_RESOURCE))
        elif isinstance(expr[2], nodes.Uri) and \
             expr[2].uri == commonns.rdf.subject:
            rel = sqlnodes.SqlRelation(1, 'statements')
            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              nodes.Uri(self.versionUri + '1'),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              uriValueRef(1, 'id', self.stmtMapping),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              nodes.Literal(commonns.rdf.subject),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(1, 'subject'),
                              nodes.Literal(TYPE_ID_RESOURCE))
        elif isinstance(expr[2], nodes.Uri) and \
             expr[2].uri == commonns.rdf.predicate:
            rel = sqlnodes.SqlRelation(1, 'statements')
            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              nodes.Uri(self.versionUri + '1'),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              uriValueRef(1, 'id', self.stmtMapping),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              nodes.Literal(commonns.rdf.predicate),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(1, 'predicate'),
                              nodes.Literal(TYPE_ID_RESOURCE))
        elif isinstance(expr[2], nodes.Uri) and \
             expr[2].uri == commonns.rdf.object:
            rel = sqlnodes.SqlRelation(1, 'statements')
            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              nodes.Uri(self.versionUri + '1'),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              uriValueRef(1, 'id', self.stmtMapping),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              nodes.Literal(commonns.rdf.object),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(1, 'object'),
                              sqlnodes.SqlFieldRef(1, 'object_type'))

        if replExpr is not None:
            return (replExpr,
                    ('context', 'subject', 'predicate', 'object'))
        else:
            return super(MetaVersionMapper, self).replStatementPattern(expr)

    def replReifStmtPattern(self, expr):
        if self.reifStmtRepl is not None:
            return self.reifStmtRepl

        rel = sqlnodes.SqlRelation(1, 'statements')

        replExpr = \
          nodes.MapResult(['context', 'type__context',
                           'stmt', 'type__stmt',
                           'subject', 'type__subject',
                           'predicate', 'type__predicate',
                           'object', 'type__object'],
                          rel,
                          nodes.Uri(self.versionUri + '1'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          uriValueRef(1, 'id', self.stmtMapping),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          checksumValueRef(1, 'subject'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          checksumValueRef(1, 'predicate'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          checksumValueRef(1, 'object'),
                          sqlnodes.SqlFieldRef(1, 'object_type'))

        self.reifStmtRepl = (replExpr,
            ('context', 'stmt', 'subject', 'predicate', 'object'))

        return self.reifStmtRepl


compMapping = UriValueMapping(commonns.relrdf.comp)


class TwoWayComparisonMapper(BasicMapper,
                             transform.StandardReifTransformer):
    """Targets an abstract query to a context set presenting two
    versions (versions A and B) as three contexts: one containing the
    statements only in A, one containing the statements only in B, and
    one containing the statements common to both versions."""
    
    __slots__ = ('versionA',
                 'versionB')

    name = "Two Way Comparision"
    parameterInfo = ({"name":"versionA", "label":"Version A", "tip":"Enter version 1 to compare", "assert":"versionA!=''", "asserterror":"Version must not be empty"},
                     {"name":"versionB", "label":"Version B", "tip":"Enter version 2 to compare", "assert":"versionB!=''", "asserterror":"Version must not be empty"})

    def __init__(self, versionA, versionB):
        super(TwoWayComparisonMapper, self).__init__()

        self.versionA = int(versionA)
        self.versionB = int(versionB)

        # Cache for the statement pattern replacement expression.
        self.stmtRepl = None

    def prepareConnection(self, connection):
        cursor = connection.cursor()

        # We create a temporary table for the comparison statements.
        # FIXME: The table must be named in such a way that collisions
        # are avoid between multiple database conections.
        cursor.execute(
            """
            DROP TABLE IF EXISTS comparison
            """)
        cursor.execute(
            """
            CREATE TABLE comparison (
              stmt_id integer unsigned NOT NULL,
              context char(2) NOT NULL,
              PRIMARY KEY (stmt_id),
              KEY (context)
            ) ENGINE=MyISAM DEFAULT CHARSET=utf8;
            """)

        # This is a pretty sui generis way of performing the actual
        # comparison, but MySQL doesn't have a full outer join, and
        # this solution not only works properly but seems to be very
        # efficient. Notice that it relies on the fact that version
        # numbers are never 0. The IF expressions inside the sum are
        # necessary to guarantee correct results when versionA and
        # versionB are equal.
        cursor.execute(
            """
              INSERT INTO comparison
                SELECT
                  v.stmt_id AS stmt_id,
                  CASE sum(IF(v.version_id = %d, 1, 0) +
                           IF(v.version_id = %d, 2, 0))
                    WHEN 1 THEN "A"
                    WHEN 2 THEN "B"
                    WHEN 3 THEN "AB"
                  END AS context
                FROM version_statement v
                WHERE v.version_id = %d or v.version_id = %d
                GROUP BY v.stmt_id
            """ % (self.versionA,
                   self.versionB,
                   self.versionA,
                   self.versionB))

    def replStatementPattern(self, expr):
        # Check for complete version matching.
        if isinstance(expr[0], nodes.Uri) and \
               expr[0].uri.startswith(commonns.relrdf.model) and \
               len(expr[0].uri) == len(commonns.relrdf.model) + 1 and \
               expr[0].uri[len(commonns.relrdf.model)] in ('A', 'B'):
            modelLetter = expr[0].uri[len(commonns.relrdf.model)]
            if modelLetter == 'A':
                versionId = self.versionA
            else:
                versionId = self.versionB

            rel = build.buildExpression(
                (nodes.Select,
                 (nodes.Product,
                  (sqlnodes.SqlRelation, 1, 'version_statement'),
                  (sqlnodes.SqlRelation, 2, 'statements')),
                 (nodes.And,
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'version_id'),
                   (nodes.Literal, versionId)),
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'stmt_id'),
                   (sqlnodes.SqlFieldRef, 2, 'id'))))
                )

            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              nodes.Uri(commonns.relrdf.model + modelLetter),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(2, 'subject'),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(2, 'predicate'),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(2, 'object'),
                              sqlnodes.SqlFieldRef(2, 'object_type'))
        else:
            rel = build.buildExpression(
                (nodes.Select,
                 (nodes.Product,
                  (sqlnodes.SqlRelation, 1, 'comparison'),
                  (sqlnodes.SqlRelation, 2, 'statements')),
                 (nodes.Equal,
                  (sqlnodes.SqlFieldRef, 1, 'stmt_id'),
                  (sqlnodes.SqlFieldRef, 2, 'id')))
                )

            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              uriValueRef(1, 'context', compMapping),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(2, 'subject'),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(2, 'predicate'),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(2, 'object'),
                              sqlnodes.SqlFieldRef(2, 'object_type'))

        return (replExpr,
                ('context', 'subject', 'predicate', 'object'))


class ThreeWayComparisonMapper(BasicMapper,
                               transform.StandardReifTransformer):
    """Targets an abstract query to a context set presenting three
    versions (versions A, B and C) as seven contexts, corresponding to
    all combinations of being in A, B, and/or C."""
    
    __slots__ = ('versionA',
                 'versionB',
                 'versionC')

    name = "Three Way Comparision"
    parameterInfo = ({"name":"versionA", "label":"Version A", "tip":"Enter version 1 to compare", "assert":"versionA!=''", "asserterror":"Version must not be empty"},
                     {"name":"versionB", "label":"Version B", "tip":"Enter version 2 to compare", "assert":"versionB!=''", "asserterror":"Version must not be empty"},
                     {"name":"versionC", "label":"Version C", "tip":"Enter version 3 to compare", "assert":"versionC!=''", "asserterror":"Version must not be empty"})

    def __init__(self, versionA, versionB, versionC):
        super(ThreeWayComparisonMapper, self).__init__()

        self.versionA = int(versionA)
        self.versionB = int(versionB)
        self.versionC = int(versionC)

        # Cache for the statement pattern replacement expression.
        self.stmtRepl = None

    def prepareConnection(self, connection):
        cursor = connection.cursor()

        # We create a temporary table for the comparison statements.
        # FIXME: The table must be named in such a way that collisions
        # are avoid between multiple database conections.
        cursor.execute(
            """
            DROP TABLE IF EXISTS comparison
            """)
        cursor.execute(
            """
            CREATE TABLE comparison (
              stmt_id integer unsigned NOT NULL,
              context char(3) NOT NULL,
              PRIMARY KEY (stmt_id),
              KEY (context)
            ) ENGINE=MyISAM DEFAULT CHARSET=utf8;
            """)

        # This is a pretty sui generis way of performing the actual
        # comparison, but MySQL doesn't have a full outer join, and
        # this solution not only works properly but seems to be very
        # efficient. Notice that it relies on the fact that version
        # numbers are never 0. The IF expressions inside the sum are
        # necessary to guarantee correct results when versionA,
        # versionB and versionC are not all different from each other.
        cursor.execute(
            """
              INSERT INTO comparison
                SELECT
                  v.stmt_id AS stmt_id,
                  CASE
                      sum(IF(v.version_id = %d, 1, 0) +
                          IF(v.version_id = %d, 2, 0) +
                          IF(v.version_id = %d, 4, 0))
                    WHEN 1 THEN "A"
                    WHEN 2 THEN "B"
                    WHEN 3 THEN "AB"
                    WHEN 4 THEN "C"
                    WHEN 5 THEN "AC"
                    WHEN 6 THEN "BC"
                    WHEN 7 THEN "ABC"
                  END AS context
                FROM version_statement v
                WHERE v.version_id = %d or v.version_id = %d
                      or v.version_id = %d
                GROUP BY v.stmt_id
            """ % (self.versionA,
                   self.versionB,
                   self.versionC,
                   self.versionA,
                   self.versionB,
                   self.versionC))

    def replStatementPattern(self, expr):
        # Check for complete version matching.
        if isinstance(expr[0], nodes.Uri) and \
               expr[0].uri.startswith(commonns.relrdf.model) and \
               len(expr[0].uri) == len(commonns.relrdf.model) + 1 and \
               expr[0].uri[len(commonns.relrdf.model)] in ('A', 'B', 'C'):
            modelLetter = expr[0].uri[len(commonns.relrdf.model)]
            if modelLetter == 'A':
                versionId = self.versionA
            elif modelLetter == 'B':
                versionId = self.versionB
            else:
                versionId = self.versionC

            rel = build.buildExpression(
                (nodes.Select,
                 (nodes.Product,
                  (sqlnodes.SqlRelation, 1, 'version_statement'),
                  (sqlnodes.SqlRelation, 2, 'statements')),
                 (nodes.And,
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'version_id'),
                   (nodes.Literal, versionId)),
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'stmt_id'),
                   (sqlnodes.SqlFieldRef, 2, 'id'))))
                )

            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              nodes.Uri(commonns.relrdf.model + modelLetter),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(2, 'subject'),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(2, 'predicate'),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(2, 'object'),
                              sqlnodes.SqlFieldRef(2, 'object_type'))
        else:
            rel = build.buildExpression(
                (nodes.Select,
                 (nodes.Product,
                  (sqlnodes.SqlRelation, 1, 'comparison'),
                  (sqlnodes.SqlRelation, 2, 'statements')),
                 (nodes.Equal,
                  (sqlnodes.SqlFieldRef, 1, 'stmt_id'),
                  (sqlnodes.SqlFieldRef, 2, 'id')))
                )

            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              uriValueRef(1, 'context', compMapping),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(2, 'subject'),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(2, 'predicate'),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              checksumValueRef(2, 'object'),
                              sqlnodes.SqlFieldRef(2, 'object_type'))

        return (replExpr,
                ('context', 'subject', 'predicate', 'object'))


class Results(object):
    __slots__ = ('cursor',
                 'columnNames',
                 'length')

    def __init__(self, connection, columnNames, sqlText):
        self.columnNames = columnNames

        self.cursor = connection.cursor()

        # Send the query to the database (iterating on this object
        # will produce the actual results.)
        self.cursor.execute(sqlText)

        self.length = self.cursor.rowcount

    def iterAll(self):
        row = self.cursor.fetchone()
        while row is not None:
            result = []
            for rawValue, typeId in zip(row[0::2], row[1::2]):
                result.append(self._convertResult(rawValue, typeId))
            yield tuple(result)

            row = self.cursor.fetchone()

    __iter__ = iterAll

    def __len__(self):
        return self.length

    def _convertResult(self, rawValue, typeId):
        if isinstance(rawValue, str):
            try:
                rawValue = rawValue.decode('utf8')
            except UnicodeDecodeError:
                rawValue = "<<Character encoding error>>"

        # FIXME: This must be converted to using type names.
        if rawValue is None:
            value = None
        elif typeId == 1:
            value = uri.Uri(rawValue)
        elif typeId == 2:
            value = blanknode.BlankNode(rawValue)
        elif typeId == 3:
            value = literal.Literal(rawValue)
        else:
            # Not correct.
            value = literal.Literal(rawValue)

        return value

    def __del__(self):
        self.cursor.close()


class Model(object):
    __slots__ = ('connection',
                 'mappingTransf',
                 'modelArgs',
                 '_prefixes')

    def __init__(self, connection, mappingTransf, **modelArgs):
        self.connection = connection
        self.mappingTransf = mappingTransf
        self.modelArgs = modelArgs

        # Get the prefixes from the data base. We store them in the
        # object and add them to the model args.
        cursor = self.connection.cursor()
        cursor.execute("""
        SELECT p.prefix, p.namespace
        FROM prefixes p""")

        self._prefixes = {}
        paramPrf = modelArgs.get('prefixes', {})

        row = cursor.fetchone()
        while row is not None:
            (prefix, namespace) = row
            self._prefixes[prefix] = uri.Namespace(namespace)
            paramPrf[prefix] = uri.Namespace(namespace)
            row = cursor.fetchone()

        # Add the prefixes to the modelArgs, so that the parser
        # receives them.
        modelArgs['prefixes'] = paramPrf

        # Prepare the connection for this mapping.
        self.mappingTransf.prepareConnection(self.connection)

    def query(self, queryLanguage, queryText, fileName=_("<unknown>")):
        # Parse the query.
        parser = parserfactory.getQueryParser(queryLanguage,
                                              **self.modelArgs)
        expr = parser.parse(queryText, fileName)

        # Convert the parsed expression to SQL:

        # Add explicit type columns to results.
        transf = transform.ExplicitTypeTransformer()
        expr = transf.process(expr)

        # Add dynamic type checks.
        transf = dynamic.DynTypeCheckTransl()
        expr = transf.process(expr)

        # Apply the selected mapping.
        expr = self.mappingTransf.process(expr)

        # Dereference value references from the mapping.
        transf = valueref.ValueRefDereferencer()
        expr = transf.process(expr)

        # Generate SQL.
        sqlText = emit.emit(expr)

        # Find out the column names.
        namesExpr = expr
        while not hasattr(namesExpr, 'columnNames'):
            namesExpr = namesExpr[0]

        # Build a Results object with the obtained SQL query.
        return Results(self.connection, list(namesExpr.columnNames[::2]),
                       sqlText.encode('utf-8'))

    def getPrefixes(self):
        return self._prefixes

    def __del__(self):
        # Release mapping specific resources.
        self.mappingTransf.releaseConnection(self.connection)

        self.connection.close()


_modelFactories = {
    'metaversion': MetaVersionMapper,
    'singleversion': SingleVersionMapper,
    'allversions': AllVersionsMapper,
    'twoway': TwoWayComparisonMapper,
    'threeway': ThreeWayComparisonMapper
    }

def getModel(connection, modelType, schema=None, **modelArgs):
    modelTypeNorm = modelType.lower()

    if schema is not None:
        # Try to load the schema.
        schema = mapping.loadSchema(schema)
        if schema is None:
            raise InstantiationError(_("Schema '%s' not found") % schema)

        transf = schema.getMapper(modelType, **modelArgs)
    else:
        try:
            transf = _modelFactories[modelTypeNorm](**modelArgs)
        except KeyError:
            raise InstantiationError(_("Invalid model type '%s'") % modelType)
        except TypeError, e:
            raise InstantiationError(_("Missing or invalid model "
                                       "arguments: %s") % e)

    return Model(connection, transf, **modelArgs)
