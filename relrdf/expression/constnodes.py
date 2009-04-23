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


"""Utility operations to work with constant nodes (nodes.Literal or
nodes.Uri) and lists of constant nodes."""

import nodes


def isConstNode(expr):
    return isinstance(expr, nodes.Uri) or \
           isinstance(expr, nodes.Literal)

def constValue(expr):
    if isinstance(expr, nodes.Uri):
        return expr.uri
    elif isinstance(expr, nodes.Literal):
        return expr.literal.value
    return None

def constValues(exprs, all=False):
    for expr in exprs:
        if isinstance(expr, nodes.Uri):
            yield expr.uri
        elif isinstance(expr, nodes.Literal):
            yield expr.literal.value
        elif all:
            raise ValueError

def nonConstExprs(exprs):
    for expr in exprs:
        if not isConstNode(expr):
            yield expr
