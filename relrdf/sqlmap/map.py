"""SQL mapping objects."""

from relrdf.expression import uri, blanknode, literal
from relrdf.expression import simplify

import transform
import emit


class SqlMapper(object):
    __slots__ = ('sqlTransf',)

    def __init__(self, sqlTransf):
        self.sqlTransf = sqlTransf
        
    def mapExpr(self, expr):
        transf = transform.ExplicitTypeTransformer()
        expr = transf.process(expr)

        expr = self.sqlTransf.process(expr)

        expr = simplify.simplify(expr)

        return emit.emit(expr)

    def convertResult(self, rawValue, typeId):
        if isinstance(rawValue, str):
            try:
                rawValue = rawValue.decode('utf8')
            except UnicodeDecodeError:
                print "Error:", tuple(rawValue)
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


class SingleVersionMapper(SqlMapper):
    __slots__ = ()

    def __init__(self, versionId):
        transf = transform.SingleVersionSqlTransformer(int(versionId))
        super(SingleVersionMapper, self).__init__(transf)


class AllVersionsMapper(SqlMapper):
    __slots__ = ()

    def __init__(self):
        transf = transform.AllVersionsSqlTransformer()
        super(AllVersionsMapper, self).__init__(transf)


class TwoWayComparisonMapper(SqlMapper):
    __slots__ = ()

    def __init__(self, versionA, versionB):
        transf = transform.TwoWayComparisonSqlTransformer(int(versionA),
                                                          int(versionB))
        super(TwoWayComparisonMapper, self).__init__(transf)


