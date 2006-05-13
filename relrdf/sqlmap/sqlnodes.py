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
        stream.write(' %s %d' % (self.sqlCode, self.incarnation))


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


class SqlExprValueRef(valueref.ValueRef):
    """A value reference pointing to a value whose internal
    representation is an incarnation field, that can be converted back
    and forth to and from its external representation using SQL
    expressions."""

    __slots__ = ('incarnation',
                 'fieldId',
                 'intToExt',
                 'extToInt')

    def __init__(self, mappingType, incarnation, fieldId, intToExt, extToInt):
        super(SqlExprValueRef, self).__init__(mappingType)

        self.incarnation = incarnation
        self.fieldId = fieldId
        self.intToExt = intToExt
        self.extToInt = extToInt

    def getInternal(self):
        return SqlFieldRef(self.incarnation, self.fieldId)

    def getExternal(self):
        return SqlScalarExpr(self.intToExt,
                             self.getInternal())

    def getConvertToInternal(self, expr):
        return SqlScalarExpr(self.extToInt, expr)

    def attributesRepr(self):
        return '%s, %s, %s, %s' % (repr(self.incarnation),
                                   repr(self.fieldId),
                                   repr(self.intToExt),
                                   repr(self.extToInt))

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.attributesRepr())

