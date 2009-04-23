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


from relrdf.expression import nodes


class GraphPattern(nodes.ExpressionNode):
    """An expression node representing an SPARQL graph pattern."""

    __slots__ = ()


class OpenUnion(nodes.ExpressionNode):
    """An expression node representing an SPARQL "open" (without fixed
    columns) pattern union operation."""

    __slots__ = ()


class Optional(nodes.ExpressionNode):
    """An expression node representing an SPARQL optional pattern."""

    __slots__ = ()

    def __init__(self, pattern):
        super(Optional, self).__init__(pattern)


class Filter(nodes.ExpressionNode):
    """An expression node representing an SPARQL filter."""

    __slots__ = ()

    def __init__(self, cond):
        super(Filter, self).__init__(cond)


