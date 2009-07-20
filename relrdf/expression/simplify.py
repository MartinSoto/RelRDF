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


import nodes
import rewrite


def reduceUnary(expr, default=None):
    """Reduce an expression to the value of `default` if it has no
    subexpressions, and to its subexpression if it has only
    one. Otherwise return the expression unmodified."""
    if len(expr) == 0:
        return default, True
    elif len(expr) == 1:
        return expr[0], True
    else:
        return expr, False

def flattenAssoc(nodeType, expr):
    modif = False
    i = 0
    while i < len(expr):
        subexpr = expr[i]
        if isinstance(subexpr, nodeType):
            expr[i:i+1] = subexpr
            modif = True
        i += 1

    return expr, modif

def promoteSelect(expr):
    modif = False
    promoted = []
    conditions = []
    for subexpr in expr:
        if isinstance(subexpr, nodes.Select):
            promoted.append(subexpr[0])
            conditions.append(subexpr[1])
            modif = True
        else:
            promoted.append(subexpr)

    if modif:
        return (nodes.Select(nodes.Product(*promoted),
                             nodes.And(*conditions)),
                True)
    else:
        return expr, False

def flattenSelect(expr):
    modif = False
    (rel, predicate) = expr
    if not isinstance(rel, nodes.Select):
        return expr, False
    else:
        return (nodes.Select(rel[0],
                             nodes.And(rel[1], predicate)),
                True)

def promoteMapValue(expr, id):

    # Get the MapValue
    map = expr[id]
    assert isinstance(expr[id], nodes.MapValue)

    # Promote into query modifiers
    if isinstance(expr, nodes.QueryResultModifier):

        # Search for query result node
        sexpr = expr[0]
        while sexpr != None and not isinstance(sexpr, nodes.QueryResult):
            sexpr = sexpr[0];
        assert sexpr != None, "Could not find query result node!"

        # Promote
        expr[id] = map[1]
        sexpr[0] = nodes.Product(sexpr[0], map[0])
        return (expr, True)


    # Fuse with Select, MapResult or MapValue
    #  Select(r1, MapValue(r2, v))
    #  -> Select(Product(r1, r2), v)
    #  MapResult(r1, ..., MapValue(r2, v), ...)
    #  -> Select(Product(r1, r2), ..., v, ...)
    #  MapValue(r1, MapValue(r2, v))
    #  -> MapValue(Product(r1, r2), v)
    if isinstance(expr, nodes.Select) or isinstance(expr, nodes.QueryResult) or \
       isinstance(expr, nodes.MapValue):
        expr[id] = map[1]
        expr[0] = nodes.Product(expr[0], map[0])
        return (expr, True)

    # Promote out of all other expression nodes
    #  Op(..., MapValue(r, v), ...)
    #  -> MapValue(r, Op(..., v, ...))
    if isinstance(expr, nodes.ValueNode):
        expr[id] = map[1]
        map[1] = expr
        return (map, True)

    return (expr, False)


def simplifyNode(expr, subexprsModif):
    modif = True
    while modif:
        modif = False

        if isinstance(expr, nodes.Product):
            expr, m = flattenAssoc(nodes.Product, expr)
            modif = modif or m
            expr, m = promoteSelect(expr)
            modif = modif or m
        elif isinstance(expr, nodes.Or):
            expr, m = flattenAssoc(nodes.Or, expr)
            modif = modif or m
        elif isinstance(expr, nodes.And):
            expr, m = flattenAssoc(nodes.And, expr)
            modif = modif or m
        elif isinstance(expr, nodes.Union):
            expr, m = flattenAssoc(nodes.Union, expr)
            modif = modif or m
        elif isinstance(expr, nodes.Intersection):
            expr, m = flattenAssoc(nodes.Intersection, expr)
            modif = modif or m
        elif isinstance(expr, nodes.Select):
            expr, m = flattenSelect(expr)
            modif = modif or m

#        for i, subexpr in enumerate(expr):
#            if isinstance(subexpr, nodes.MapValue):
#                expr, m = promoteMapValue(expr, i)
#                if m:
#                    modif = True;
#                    break

        subexprsModif = subexprsModif or modif

    return expr, subexprsModif

def simplify(expr):
    """Simplify a expression."""

    modif = True
    while modif:
        modif = False
        expr, m = rewrite.exprApply(expr, postOp=simplifyNode)
        modif = modif or m

    return expr

