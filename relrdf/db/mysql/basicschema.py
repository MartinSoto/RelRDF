from relrdf import parserfactory, commonns

from relrdf.typecheck import dynamic
from relrdf.expression import uri, blanknode, literal, simplify, nodes, build
from relrdf.sqlmap import transform, valueref, sqlnodes, emit

from relrdf.typecheck.typeexpr import LiteralType, BlankNodeType, \
     ResourceType, RdfNodeType, resourceType, rdfNodeType


TYPE_ID_RESOURCE = literal.Literal(1)
TYPE_ID_BLANKNODE = literal.Literal(2)
TYPE_ID_LITERAL = literal.Literal(3)


class SqlUriValueRef(sqlnodes.SqlExprValueRef):
    """A value reference whose internal representation is the value of
    an incarnation field and whose external representation is an URI
    built by prepending a base URI to teh canonical string
    represnetation of the internal value."""

    __slots__ = ('baseUri',)

    def __init__(self, incarnation, fieldId, baseUri):
        self.baseUri = baseUri

        intToExt = 'CONCAT("%s", $0$)' % baseUri
        l = len(baseUri.encode('utf-8'))
        extToInt = '''
        IF(SUBSTRING($0$, 1, %d) = "%s",
           SUBSTRING($0$, %d), "<<<NO VALUE>>>")''' % (l, baseUri, l + 1)

        # We use the base URI as mapping type.
        super(SqlUriValueRef, self).\
            __init__(baseUri, incarnation, fieldId, intToExt, extToInt)


class BasicMapper(transform.PureRelationalTransformer):
    """A base mapper for the MySQL basic schema. It handles the
    mapping of type expressions."""

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
                 
                 'stmtRepl')

    def __init__(self, versionId, versionUri):
        super(BasicSingleVersionMapper, self).__init__()

        self.versionId = int(versionId)
        self.versionUri = versionUri

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
                          sqlnodes.SqlFieldRef(2, 'subject'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          sqlnodes.SqlFieldRef(2, 'predicate'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          sqlnodes.SqlFieldRef(2, 'object'),
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

    def __init__(self, versionId, versionUri=commonns.relrdf.version):
        super(SingleVersionMapper, self).__init__(versionId,
                                                  versionUri)


class AllVersionsMapper(BasicMapper,
                        transform.StandardReifTransformer):
    """Targets an abstract query to a context set whose elements are
    the versions of a model."""
    
    __slots__ = ('versionUri',

                 'stmtRepl')

    def __init__(self, versionUri=commonns.relrdf.version,
                 stmtUri=commonns.relrdf.stmt, metaInfoVersion=1):
        super(AllVersionsMapper, self).__init__()

        self.versionUri = versionUri

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
                          SqlUriValueRef(1, 'version_id', self.versionUri),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          sqlnodes.SqlFieldRef(2, 'subject'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          sqlnodes.SqlFieldRef(2, 'predicate'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          sqlnodes.SqlFieldRef(2, 'object'),
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

                 'reifStmtRepl')

    def __init__(self, versionUri=commonns.relrdf.version,
                 stmtUri=commonns.relrdf.stmt):
        super(MetaVersionMapper, self).__init__(1, versionUri)

        self.stmtUri = stmtUri

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
                              SqlUriValueRef(1, 'id', self.stmtUri),
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
                              SqlUriValueRef(1, 'version_id',
                                             self.versionUri),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              nodes.Literal(commonns.relrdf. \
                                            versionContainsStmt),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              SqlUriValueRef(1, 'stmt_id',
                                             self.stmtUri),
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
                              SqlUriValueRef(1, 'id', self.stmtUri),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              nodes.Literal(commonns.rdf.subject),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              sqlnodes.SqlFieldRef(1, 'subject'),
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
                              SqlUriValueRef(1, 'id', self.stmtUri),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              nodes.Literal(commonns.rdf.predicate),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              sqlnodes.SqlFieldRef(1, 'predicate'),
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
                              SqlUriValueRef(1, 'id', self.stmtUri),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              nodes.Literal(commonns.rdf.object),
                              nodes.Literal(TYPE_ID_RESOURCE),
                              sqlnodes.SqlFieldRef(1, 'object'),
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
                          SqlUriValueRef(1, 'id', self.stmtUri),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          sqlnodes.SqlFieldRef(1, 'subject'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          sqlnodes.SqlFieldRef(1, 'predicate'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          sqlnodes.SqlFieldRef(1, 'object'),
                          sqlnodes.SqlFieldRef(1, 'object_type'))

        self.reifStmtRepl = (replExpr,
            ('context', 'stmt', 'subject', 'predicate', 'object'))

        return self.reifStmtRepl


class TwoWayComparisonMapper(BasicMapper,
                             transform.StandardReifTransformer):
    """Targets an abstract query to a context set presenting two
    versions (versions A and B) as three contexts: one containing the
    statements only in A, one containing the statements only in B, and
    one containing the statements common to both versions."""
    
    __slots__ = ('versionA',
                 'versionB',

                 'stmtRepl')

    def __init__(self, versionA, versionB):
        super(TwoWayComparisonMapper, self).__init__()

        self.versionA = int(versionA)
        self.versionB = int(versionB)

        # Cache for the statement pattern replacement expression.
        self.stmtRepl = None

    def replStatementPattern(self, expr):
        if self.stmtRepl is not None:
            return self.stmtRepl

        # This is a pretty sui generis way of doing this, but MySQL
        # doesn't have a full outer join, and this solution not only
        # works properly but seems to optimize quite well. Notice that
        # it relies on the fact that versions numbers are never 0.
        rel = sqlnodes.SqlRelation(
            1,
            """
            select
              comp.context as context,
              s.subject as subject,
              s.predicate as predicate,
              s.object_type as object_type,
              s.object as object
            from
              ( select
                  case sum(v.version_id)
                    when %d then "A"
                    when %d then "B"
                    when %d then "AB"
                  end as context,
                  v.stmt_id as stmt_id
                from version_statement v
                where v.version_id = %d or v.version_id = %d
                group by v.stmt_id) as comp,
              statements s
            where
              comp.stmt_id = s.id
            """ % (self.versionA,
                   self.versionB,
                   self.versionA + self.versionB,
                   self.versionA,
                   self.versionB))
                     
        replExpr = \
          nodes.MapResult(['context', 'type__context',
                           'subject', 'type__subject',
                           'predicate', 'type__predicate',
                           'object', 'type__object'],
                          rel,
                          SqlUriValueRef(1, 'context',
                                         commonns.relrdf.comp),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          sqlnodes.SqlFieldRef(1, 'subject'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          sqlnodes.SqlFieldRef(1, 'predicate'),
                          nodes.Literal(TYPE_ID_RESOURCE),
                          sqlnodes.SqlFieldRef(1, 'object'),
                          sqlnodes.SqlFieldRef(1, 'object_type'))

        self.stmtRepl = (replExpr,
                         ('context', 'subject', 'predicate', 'object'))

        return self.stmtRepl


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
                rawValue = "ERROR"

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

        # Simplify the expression.
        expr = simplify.simplify(expr)

        # Generate SQL.
        sqlText = emit.emit(expr)

        # Build a Results objects with the resulting SQL query.
        return Results(self.connection, list(expr.columnNames[::2]),
                       sqlText.encode('utf-8'))

    def getPrefixes(self):
        return self._prefixes

    def __del__(self):
        self.connection.close()


_modelFactories = {
    'metaversion': MetaVersionMapper,
    'singleversion': SingleVersionMapper,
    'allversions': AllVersionsMapper,
    'twoway': TwoWayComparisonMapper
    }

def getModel(connection, modelType, **modelArgs):
    modelTypeNorm = modelType.lower()

    try:
        transf = _modelFactories[modelTypeNorm](**modelArgs)
    except KeyError:
        assert False, "invalid model type '%s'" % modelType

    return Model(connection, transf, **modelArgs)
