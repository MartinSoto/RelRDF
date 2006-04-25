from relrdf.expression import nodes

class SqlRelation(nodes.ExpressionNode):
    """An expression node corresponding to an SQL expression producing
    a relation, with incarnation."""

    __slots__ = ('incarnation',
                 'sqlCode')

    def __init__(self, incarnation, sqlCode, *codeParams):
        super(SqlRelation, self).__init__()

        self.incarnation = incarnation
        self.sqlCode = sqlCode % codeParams

    def attributesRepr(self):
        return '%s, %s' % (repr(self.sqlCode), repr(self.incarnation))

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s %d' % (self.sqlCode, self.incarnation))


class SqlFieldRef(nodes.ExpressionNode):
    """A reference to one particular field of a particular relation
    (incarnation) tuple."""

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


