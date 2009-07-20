# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2009 Fraunhofer-Institut fuer Experimentelles
#                         Software Engineering (IESE).
#
# RelRDF is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.


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

    # An integer value used to decide which one of two or more
    # mappings to use when comparing.
    weight = 50

    def intToExt(self, internal):
        """Given an expression corresponding to the internal
        representation of a value, construct an expression
        corresponding to its external representation."""
        return NotImplemented

    def extToInt(self, external):
        """Given an expression corresponding to the external
        representation of a value, construct an expression
        corresponding to its internal representation."""

class ValueRef(nodes.ExpressionNode):
    """An expression node packaging an internal value.

    A `ValueRef` has two subexpressions. The first subexpression is
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
        internal values whenever possible, and when not possible, by
        picking a mapping based on its defined weight. This is
        necessary in order for the underlying database to be able to
        optimize certain select and join operations.

        Notice that giving priority to a certain type of mapping is
        not ideal, because the optimal solution depends on the join
        order. This is, however, the best we can do as long as we
        don't have our own optimizer."""

        # First, find the heaviest mapping.
        mapping = None
        for subexpr in subexprs:
            if isinstance(subexpr, ValueRef) and \
                  (mapping is None or subexpr[0].weight > mapping.weight):
                mapping = subexpr[0]

        if mapping is None:
            # No value references in the comparison.
            return expr

        for i, subexpr in enumerate(subexprs):
            if isinstance(subexpr, ValueRef):
                if isinstance(subexpr[0], type(mapping)):
                    expr[i] = subexpr[1]
                else:
                    expr[i] = mapping.extToInt(subexpr[0].intToExt(subexpr[1]))
            else:
                expr[i] = mapping.extToInt(subexpr)

        return expr

    Equal = _comparisonExpr
    Different = _comparisonExpr
