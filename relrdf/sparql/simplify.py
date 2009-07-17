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


import operator

from relrdf.expression.simplify import flattenAssoc, flattenSelect, \
    reduceUnary
from relrdf.expression import nodes, rewrite


def simplifySelect(expr):
    subexpr = expr[0]
    if isinstance(subexpr, nodes.Empty):
        # Selecting on the empty set always yields the empty set.
        return subexpr, True
    else:
        return expr, False

def simplifyJoin(expr):
    if len(expr) == 1:
        return expr[0], True
    elif reduce(operator.__or__,
                  (isinstance(subexpr, nodes.Empty) for subexpr in expr)):
        # There's at least one empty relation in the join.
        return nodes.Empty(), True
    else:
        return expr, False

def simplifyLeftJoin(expr):
    subexpr = expr[0]
    if isinstance(subexpr, nodes.Empty):
        # Left-joining the empty set with anything always produces the
        # empty set.
        return subexpr, True

    subexpr = expr[1]
    if isinstance(subexpr, nodes.Empty):
        # Left-joining anything with the empty set produces the same
        # thing (trivially, no element on the left side will have a
        # counterpart on the right side).
        return expr[0], True

    return expr, False

def simplifyNode(expr, subexprsModif):
    """Simplify a SPARQL node."""
    modif = True
    while modif:
        modif = False

        if isinstance(expr, nodes.Or):
            expr, m = flattenAssoc(nodes.Or, expr)
            modif = modif or m
            expr, m = reduceUnary(expr)
            modif = modif or m
        elif isinstance(expr, nodes.And):
            expr, m = flattenAssoc(nodes.And, expr)
            modif = modif or m
            expr, m = reduceUnary(expr)
            modif = modif or m
        elif isinstance(expr, nodes.Select):
            expr, m = flattenSelect(expr)
            modif = modif or m
            expr, m = reduceUnary(expr)
            modif = modif or m
            expr, m = simplifySelect(expr)
            modif = modif or m
        elif isinstance(expr, nodes.Join):
            expr, m = simplifyJoin(expr)
            modif = modif or m
        elif isinstance(expr, nodes.LeftJoin):
            expr, m = simplifyLeftJoin(expr)
            modif = modif or m
        elif isinstance(expr, nodes.Union):
            expr, m = flattenAssoc(nodes.Union, expr)
            modif = modif or m
            expr, m = reduceUnary(expr)
            modif = modif or m
        
        subexprsModif = subexprsModif or modif
    
    return expr, subexprsModif

def simplify(expr):
    """Simplify a SPARQL expression."""

    modif = True
    while modif:
        modif = False
        expr, m = rewrite.exprApply(expr, postOp=simplifyNode)
        modif = modif or m

    return expr
