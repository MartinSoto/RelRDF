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


class Explicit(object):
    __slots__ = ('wrapped')

    def __init__(self, wrapped):
        self.wrapped = wrapped


def buildExpression(exprIter):
    """Builds an expression from an expression iterable.

    An expression iterable is in iterable object whose first element
    is a constructor function for a expression node and whose
    subsequent elements are intended to define the constructor
    parameters. If such elements are iterable, they will be fed
    recursively to this function in order to build the actual
    parameter value. If they are not iterable, they will be passed
    directly as parameters. In order to pass iterable values directly
    as parameters, they can be wrapped using the `Explicit` class in
    this module."""

    it = iter(exprIter)
    constr = it.next()
    params = list(it)

    for i, p in enumerate(params):
        if isinstance(p, Explicit):
            params[i] = p.wrapped
        elif hasattr(p, '__iter__'):
             params[i] = buildExpression(p)

    return constr(*params)

