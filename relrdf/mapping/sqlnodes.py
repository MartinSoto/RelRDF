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

import valueref


class SqlRelation(nodes.ExpressionNode):
    """An expression node corresponding to an SQL expression producing
    a relation, with incarnation."""

    __slots__ = ('incarnation',
                 'sqlCode')

    def __init__(self, incarnation, sqlCode):
        super(SqlRelation, self).__init__()

        self.incarnation = incarnation
        self.sqlCode = sqlCode

    def attributesRepr(self):
        return '%s, %s' % (repr(self.sqlCode), repr(self.incarnation))

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s %s' % (self.sqlCode, self.incarnation))


class SqlFieldRef(nodes.ExpressionNode):
    """A reference to one particular field of a particular relation
    (incarnation)."""

    __slots__ = ('incarnation',
                 'fieldId')

    def __init__(self, incarnation, fieldId):
        super(SqlFieldRef, self).__init__()

        self.incarnation = incarnation
        self.fieldId = fieldId

    def attributesRepr(self):
        return '%s, %s' % (repr(self.incarnation),
                           repr(self.fieldId))

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.attributesRepr())


class SqlFunctionCall(nodes.ExpressionNode):
    """A SQL function call."""

    __slots__ = ('name')

    def __init__(self, name, *params):
        super(SqlFunctionCall, self).__init__(*params)
        self.name = name

    def attributesRepr(self):
        return '%s' % (repr(self.name))

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.name)



class SqlScalarExpr(nodes.ExpressionNode):
    """An expression node corresponding to a SQL expression producing
    an scalar value.

    The SQL text passed to the constructor may contain references of
    the form '$n$ where <n> is an non-negative integer. Such
    references are intended to be replaced by the SQL code generated
    for the n-th subexpression of this node."""

    __slots__ = ('sqlExpr')

    def __init__(self, sqlExpr, *subexprs):
        super(SqlScalarExpr, self).__init__(*subexprs)

        self.sqlExpr = sqlExpr

    def attributesRepr(self):
        return '%s' % (repr(self.sqlExpr))

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.sqlExpr)

