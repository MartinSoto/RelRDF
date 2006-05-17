from relrdf import parserfactory, commonns

from relrdf.expression import uri, blanknode, literal, simplify, nodes, build
from relrdf.sqlmap import map, transform, valueref, sqlnodes, emit


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


class SingleVersionMapper(transform.StandardReifTransformer,
                          transform.SqlDynTypeTransformer):
    """Targets an abstract query to a context set whith only one
    element corresponding to a single version of a model."""
    
    __slots__ = ('versionNumber',
                 'versionUri',
                 
                 'stmtRepl')

    def __init__(self, versionNumber, versionUri=commonns.relrdf.version):
        super(SingleVersionMapper, self).__init__()

        self.versionNumber = versionNumber
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
               (nodes.Literal, self.versionNumber)),
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
                          nodes.Uri(self.versionUri + str(self.versionNumber)),
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


class AllVersionsMapper(transform.StandardReifTransformer,
                        transform.SqlDynTypeTransformer):
    """Targets an abstract query to context set whose elements are all
    available versions of a model."""
    
    __slots__ = ('versionUri',

                 'stmtRepl')

    def __init__(self, versionUri=commonns.relrdf.version):
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


class TwoWayComparisonMapper(transform.StandardReifTransformer,
                             transform.SqlDynTypeTransformer):
    """Targets an abstract query to a context set presenting two
    versions (versions A and B) as three contexts: one containing the
    statements only in A, one containing the statements only in B, and
    one containing the statements common to both versions."""
    
    __slots__ = ('aVersionNumber',
                 'bVersionNumber',

                 'stmtRepl')

    def __init__(self, aVersionNumber, bVersionNumber):
        super(TwoWayComparisonMapper, self).__init__()

        self.aVersionNumber = aVersionNumber
        self.bVersionNumber = bVersionNumber

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
            """ % (self.aVersionNumber,
                   self.bVersionNumber,
                   self.aVersionNumber + self.bVersionNumber,
                   self.aVersionNumber,
                   self.bVersionNumber))
                     
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
        if typeId == 1:
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

        # Add explicit typing.
        transf = transform.ExplicitTypeTransformer()
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
        

def getModel(connection, modelType, **modelArgs):
    modelTypeNorm = modelType.lower()

    if modelTypeNorm == 'singleversion':
        transf = SingleVersionMapper(int(modelArgs['versionId']))
    elif modelTypeNorm == 'allversions':
        transf = AllVersionsMapper()
    elif modelTypeNorm == 'twoway':
        transf = TwoWayComparisonMapper(int(modelArgs['versionA']),
                                        int(modelArgs['versionB']))
    else:
        assert False, "invalid model type '%s'" % modelType

    return Model(connection, transf, **modelArgs)
