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


from relrdf.expression import nodes, rewrite

from typeexpr import commonType, LiteralType, genericLiteralType, \
     BlankNodeType, blankNodeType, ResourceType, resourceType


class DynTypeCheckTransl(rewrite.ExpressionTransformer):
    """An expression translator that adds generic dynamic type checks
    to a decoupled relational expression."""

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
            result = nodes.Type(genericLiteralType)
        elif isinstance(typeExpr, BlankNodeType):
            result = nodes.Type(blankNodeType)
        elif isinstance(typeExpr, ResourceType):
            result = nodes.Type(resourceType)
        else:
            # This expression has a generic type whose dynamic form
            # must be resolved later by the mapper.
            #
            # FIXME: Consider using another node type here instead of
            # DynType (MapperDynType?)
            result = nodes.DynType(expr)
        result.staticType = genericLiteralType # FIXME!
        return result

