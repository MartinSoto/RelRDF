from relrdf.expression import nodes, rewrite


class ValueRef(nodes.ExpressionNode):
    """An abstract expression node referencing a value stored in a SQL
    table.

    Values have an internal and an external representation. The
    internal representation corresponds to the way the value is
    actually stored in the table. The external representation is a
    string corresponding directly to an RDF value, i.e., a literal, a
    blank node label or an URI.

    For optimization purposes, it is generally better to compare
    internal representations whenever possible (this usually make it
    easier for the database to optimize joins.) The methods in this
    class are intented to support comparison of internal
    representations whenever possible."""

    __slots__ = ('mappingType')

    def __init__(self, mappingType):
        super(ValueRef, self).__init__()

        # A token to unambiguously identify the type of internal <-->
        # external mapping type performed by this object.
        self.mappingType = mappingType

    def getInternal(self):
        """Build an expression corresponding to the internal
        representation of the referenced value."""
        raise NotImplementedError

    def getExternal(self):
        """Build an expression corresponding to the external
        representation of the referenced value."""
        raise NotImplementedError

    def getConvertToInternal(self, expr):
        """Build an expression capable of converting `expr`, an
        expression producing an external representation, into its
        corresponding internal representation.

        `expr` must be copied whenever used as part of the produced
        value."""


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
                expr[i] = subexpr.getExternal()
            else:
                expr[i] = subexpr

        return expr

    def _comparisonExpr(self, expr, *subexprs):
        """Dereference the `ValueRef` subexpressions of a comparison
        node.

        This function tries to optimize comparisons by comparing
        internal values whenever possible. This is often necessary in
        order for the database to be able to optimize certain joins."""

        # We only optimize the case where value references of the same
        # mapping type are compared, possibly mixed with some
        # constants.
        valueRef = None
        for subexpr in subexprs:
            if isinstance(subexpr, ValueRef):
                if valueRef is None:
                    valueRef = subexpr
                elif valueRef.mappingType != subexpr.mappingType:
                    # Different types of ValueRef's are mixed.
                    return self.Default(expr, *subexprs)
            elif not isinstance(subexpr, nodes.Literal) and \
                 not isinstance(subexpr, nodes.Uri):
                # A different type of expression is present.
                return self.Default(expr, *subexprs)

        if valueRef is None:
            # Only comparing constants here.
            return expr

        for i, subexpr in enumerate(subexprs):
            if isinstance(subexpr, ValueRef):
                expr[i] = subexpr.getInternal()
            elif isinstance(subexpr, nodes.Literal) or \
                 isinstance(subexpr, nodes.Uri):
                expr[i] = valueRef.getConvertToInternal(subexpr)
            else:
                expr[i] = subexpr

        return expr

    Equal = _comparisonExpr
    Different = _comparisonExpr
