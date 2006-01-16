import sys

from enum import Enum

import uri
import literal


NodeTypes = Enum(
    'NOT_SUPORTED',

    'URI',
    'LITERAL',
    'FIELD_REF',

    'COMPARISON_OP',

    'BOOLEAN_OP',

    'RELATION',

    'OPTIONAL',
    'PRODUCT',
    'SELECT',

    'PROJECT')


class ExpressionNode(object):
    """A node in a expression tree."""

    __slots__ = ('_type',
                 '_subexprs')

    def __init__(self, type, *subexprs):
        self._type = type
        self._subexprs = subexprs
        assert self._checkSubexprs()

    def _checkSubexprs(self):
        for i, subexpr in enumerate(self._subexprs):
            assert isinstance(subexpr, ExpressionNode), \
                   "subexpression %d is not an ExpressionNode" % i

        return True

    def getType(self):
        return self._type

    type = property(getType)

    def getSubexprs(self):
        return self._subexprs

    subexprs = property(getSubexprs)

    def __getitem__(self, i):
        return self._subexprs[i]

    def prettyPrint(self, stream=None, indentLevel=0):
        if stream == None:
            stream = sys.stdout

        stream.write("  " * indentLevel)
        stream.write(str(self.type))

        self.prettyPrintAttributes(stream, indentLevel)

        stream.write('\n')
        for subexpr in self._subexprs:
            subexpr.prettyPrint(stream, indentLevel + 1)

    def prettyPrintAttributes(self, stream, indentLevel):
        pass


class NotSupported(ExpressionNode):
    """An expression node representing a subexpression that is not
    currently supported by the parser."""

    __slots__ = ()

    def __init__(self):
        super(NotSupported, self).__init__(NodeTypes.NOT_SUPPORTED)


class Uri(ExpressionNode):
    """An expression node representing a URI reference."""

    __slots__ = ('uri')

    def __init__(self, uriVal):
        super(Uri, self).__init__(NodeTypes.URI)

        if isinstance(uriVal, uri.Uri):
            self.uri = uriVal
        else:
            self.uri = uri.Uri(uriVal)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.uri)


class Literal(ExpressionNode):
    """An expression node representing a RDF literal."""

    __slots__ = ('literal')

    def __init__(self, literalVal):
        super(Literal, self).__init__(NodeTypes.LITERAL)

        if isinstance(literalVal, literal.Literal):
            self.literal = literalVal
        else:
            self.literal = literal.Literal(literalVal)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.literal)


class FieldRef(ExpressionNode):
    """A reference to one particular field of a relation tuple."""

    __slots__ = ('relName',
                 'incarnation',
                 'fieldId')

    def __init__(self, relName, incarnation, fieldId):
        super(FieldRef, self).__init__(NodeTypes.FIELD_REF)

        self.relName = relName
        self.incarnation = incarnation
        self.fieldId = fieldId

    def __repr__(self):
        return '%s_%d[%s]' % (self.relName,
                               self.incarnation,
                               self.fieldId)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % str(self))


class Operation(ExpressionNode):
    """A node representing an operation."""

    __slots__ = ('operator')

    def __init__(self, operationType, operator, *operands):
        super(Operation, self).__init__(operationType, *operands)

        self.operator = operator

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.operator)


class Comparison(Operation):
    """A node representing a value comparison."""

    __slots__ = ()

    def __init__(self, operator, *operands):
        super(Comparison, self).__init__(NodeTypes.COMPARISON_OP,
                                         operator, *operands)


class BooleanOperation(Operation):
    """A node representing a boolean operation."""

    __slots__ = ()

    def __init__(self, operator, *operands):
        super(BooleanOperation, self).__init__(NodeTypes.BOOLEAN_OP,
                                               operator, *operands)


class Relation(ExpressionNode):
    """An incarnation of a given relation."""

    __slots__ = ('name',
                 'incarnation')

    def __init__(self, name, incarnation):
        super(Relation, self).__init__(NodeTypes.RELATION)

        self.name = name
        self.incarnation = incarnation

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s_%d' % (self.name, self.incarnation))


class Optional(ExpressionNode):
    """A node representing an optional relation."""

    __slots__ = ()

    def __init__(self, baseRel):
        super(Optional, self).__init__(NodeTypes.OPTIONAL, baseRel)


class Product(ExpressionNode):
    """A node representing a cartesian product of two or more
    relations."""

    __slots__ = ()

    def __init__(self, *relations):
        super(Product, self).__init__(NodeTypes.PRODUCT, *relations)


class Select(ExpressionNode):
    """A node representing an optional relation."""

    __slots__ = ()

    def __init__(self, rel, predicate):
        super(Select, self).__init__(NodeTypes.SELECT, rel, predicate)


class Project(ExpressionNode):
    """A projection of a relation to certain columns."""

    __slots___ = ('columnList')

    def __init__(self, columnList):
        super(Project, self).__init__(NodeTypes.PROJECT)

        self.columnList = columnList

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' [%s]' % ', '.join(self.columnList))


