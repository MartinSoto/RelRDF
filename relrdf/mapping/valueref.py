"""Conversion between internal and external value representations.

RDF literals and URIs stored by RelRDF have a database representation
that normally isn't equal to the textual RDF value. We call the
database representation "internal", and the RDF
representation "external".

For optimization purposes, it is generally better to compare internal
representations whenever possible, since this usually makes it easier
for the database to optimize select and join operations. The classes
in this module support conversions between internal and external
representations and their related optimizations.
"""


from relrdf.expression import nodes, rewrite


class ValueMapping(nodes.ExpressionNode):
    """Abstract convertor between internal and external value
    representations.

    For uniformity, value mappings are also expressions."""

    __slots__ = ()

    def intToExt(self, internal):
        """Given an expression corresponding to the internal
        representation of a value, construct an expression
        corresponding to its external representation."""
        return NotImplemented

    def extToInt(self, external):
        """Given an expression corresponding to the external
        representation of a value, construct an expression
        corresponding to its internal representation."""


class MacroValueMapping(ValueMapping):
    """A value mapping based on schema macro expressions.

    The mapping is a expression node with two subexpressions. The
    subexpressions must be macro closures, and correspond in order to
    the internal-to-external, and to the external-to-internal value
    conversions."""

    __slots__ = ()

    def __init__(self, intToExtCls, extToIntCls):
        super(MacroValueMapping, self).__init__(intToExtCls, extToIntCls)

    def intToExt(self, internal):
        return self.intToExtCls.expand(internal)

    def extToInt(self, external):
        return self.extToIntCls.expand(external)


class ValueRef(nodes.ExpressionNode):
    """An expression node packaging an internal value.

    A `ValueRef` has a two subexpressions. The first subexpression is
    a `ValueMapping`, which is used to convert back and forth to the
    external representation. The second subexpression evaluates to the
    internal value representation the `ValueRef` refers to."""

    __slots__ = ()

    def __init__(self, mapping, subexpr):
        super(ValueRef, self).__init__(mapping, subexpr)


class ValueRefDereferencer(rewrite.ExpressionProcessor):
    """An expression transformer that dereferences value references as
    necessary, trying to use internal values for comparison, whenever
    possible."""

    __slots__ = ()

    def Default(self, expr, *subexprs):
        """Dereference all `ValueRef` subexpressions to their external
        value."""
        for i, subexpr in enumerate(subexprs):
            if isinstance(subexpr, ValueRef):
                expr[i] = subexpr[0].intToExt(subexpr[1])
            else:
                expr[i] = subexpr

        return expr

    def _comparisonExpr(self, expr, *subexprs):
        """Dereference the `ValueRef` subexpressions of a comparison
        node.

        This function tries to optimize comparisons by comparing
        internal values whenever possible. This is necessary in order
        for the underlying database to be able to optimize certain
        select and join operations."""

        # We only optimize the case where value references using the
        # same mapping are compared, possibly mixed with constants.
        mapping = None
        for subexpr in subexprs:
            if isinstance(subexpr, ValueRef):
                if mapping is None:
                    mapping = subexpr[0]
                elif mapping != subexpr[0]:
                    # Different types of ValueRef's are mixed.
                    return self.Default(expr, *subexprs)
            elif not isinstance(subexpr, nodes.Literal) and \
                 not isinstance(subexpr, nodes.Uri):
                # A different type of expression is present.
                return self.Default(expr, *subexprs)

        if mapping is None:
            # Only comparing constants here.
            return expr

        for i, subexpr in enumerate(subexprs):
            if isinstance(subexpr, ValueRef):
                expr[i] = subexpr[1]
            elif isinstance(subexpr, nodes.Literal) or \
                 isinstance(subexpr, nodes.Uri):
                expr[i] = mapping.extToInt(subexpr)
            else:
                expr[i] = subexpr

        return expr

    Equal = _comparisonExpr
    Different = _comparisonExpr
