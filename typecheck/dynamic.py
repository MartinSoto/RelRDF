from expression import nodes, rewrite

from typeexpr import commonType, LiteralType, BlankNodeType, ResourceType


class DynTypeCheckTransl(rewrite.ExpressionProcessor):
    """An expression translator that adds generic dynamic type checks
    to a relational expression."""

    __slots__ = ()

    def _addEqualTypesExpr(self, expr, *transfSubexprs):
        common = commonType(*transfSubexprs)
        if isinstance(common, BlankNodeType) or \
               isinstance(common, ResourceType):
            expr[:] = transfSubexprs
            return expr

        equalTypesExpr = nodes.Equal(*[nodes.DynType(e)
                                       for e in transfSubexprs])
        return nodes.And(equalTypesExpr, expr)

    Equal = _addEqualTypesExpr
    LessThan = _addEqualTypesExpr
    LessThanOrEqual = _addEqualTypesExpr
    GreaterThan = _addEqualTypesExpr
    GreaterThanOrEqual = _addEqualTypesExpr

    def Different(self, expr, *transfSubexprs):
        common = commonType(*transfSubexprs)
        if isinstance(common, BlankNodeType) or \
               isinstance(common, ResourceType):
            expr[:] = transfSubexprs
            return expr

        diffTypesExpr = nodes.Different(*[nodes.DynType(e)
                                          for e in transfSubexprs])
        return nodes.Or(diffTypesExpr, expr)

    def Default(self, expr, *transfSubexprs):
        expr[:] = transfSubexprs
        return expr


def addDynTypeChecks(expr):
    """Add generic runtime type checks to the statically typechecked
    expression `expr` and return the resulting expression. `expr` will
    be modified in place, but the return value must be used since the
    root node may change."""
    transl = DynTypeCheckTransl()
    return transl.process(expr)
