"""SQL mapping objects."""

from expression import uri, blanknode, literal
from expression import simplify

import transform
import emit


class VersionMapper(object):
    __slots__ = ('versionId',)

    def __init__(self, versionId):
        self.versionId = versionId
        
    def mapExpr(self, expr):
        transf = transform.ExplicitTypeTransformer()
        expr = transf.process(expr)

        #transf = transform.VersionSqlTransformer(self.versionId)
        transf = transform.GlobalSqlTransformer()
        expr = transf.process(expr)

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
