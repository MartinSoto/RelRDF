"""SQL mapping objects."""

from expression import rewrite

import transform
import emit


def VersionMapper(versionId):
    def mapper(expr):
        transf = transform.AbstractSqlSqlTransformer()
        expr = transf.process(expr)

        transf = transform.VersionSqlTransformer(versionId)
        expr = transf.process(expr)

        expr = rewrite.simplify(expr)
        expr.prettyPrint()

        return emit.emit(expr)

    return mapper
