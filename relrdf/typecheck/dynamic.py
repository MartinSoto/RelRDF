from relrdf.expression import nodes, rewrite

from typeexpr import commonType, LiteralType, genericLiteralType, \
     BlankNodeType, blankNodeType, ResourceType, resourceType


class DynTypeCheckTransl(rewrite.ExpressionTransformer):
    """An expression translator that adds generic dynamic type checks
    to a relational expression."""

    __slots__ = ()

    def __init__(self):
        super(DynTypeCheckTransl, self).__init__(prePrefix='pre')

    def preDynType(self, expr):
        return (self._dynTypeExpr(expr[0]),)

    def DynType(self, expr, subexpr):
        return subexpr

    def _addEqualTypesExpr(self, expr, *transfSubexprs):
        common = commonType(*transfSubexprs)
        if isinstance(common, BlankNodeType) or \
               isinstance(common, ResourceType):
            expr[:] = transfSubexprs
            return expr

        equalTypesExpr = nodes.Equal(*[self._dynTypeExpr(e.copy())
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

        diffTypesExpr = nodes.Different(*[self._dynTypeExpr(e.copy())
                                          for e in transfSubexprs])
        return nodes.Or(diffTypesExpr, expr)

    def _dynTypeExpr(self, expr):
        typeExpr = expr.staticType

        if isinstance(typeExpr, LiteralType):
            # FIXME:Search for the actual type id.
            return nodes.Type(genericLiteralType)
        elif isinstance(typeExpr, BlankNodeType):
            return nodes.Type(blankNodeType)
        elif isinstance(typeExpr, ResourceType):
            return nodes.Type(resourceType)
        else:
            # This expression has a generic type whose dynamic form
            # must be resolved later by the mapper.
            #
            # FIXME: Consider using another node type here instead of
            # DynType (MapperDynType?)
            return nodes.DynType(expr)
