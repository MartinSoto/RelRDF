import sys

import uri
import literal


class ExpressionNode(list):
    """A node in a expression tree."""

    __slots__ = ()

    def __init__(self, *subexprs):
        super(ExpressionNode, self).__init__(subexprs)
        assert self._checkSubexprs()

    def _checkSubexprs(self):
        for i, subexpr in enumerate(self):
            assert isinstance(subexpr, ExpressionNode), \
                   "subexpression %d is not an ExpressionNode" % i

        return True

    def copyNode(self, *subexprs):
        return self.__class__(*subexprs)

    def prettyPrint(self, stream=None, indentLevel=0):
        if stream == None:
            stream = sys.stdout

        stream.write("  " * indentLevel)
        stream.write(self.__class__.__name__)

        self.prettyPrintAttributes(stream, indentLevel)

        stream.write('\n')
        for subexpr in self:
            subexpr.prettyPrint(stream, indentLevel + 1)

    def prettyPrintAttributes(self, stream, indentLevel):
        pass


class LocationNode(ExpressionNode):
    """An expression node with location information."""

    __slots__ = ('line',
                 'column',
                 'fileName')

    def __init__(self, line=None, column=None, fileName=None):
        super(LocationNode, self).__init__()

        self.line = line
        self.column = column
        self.fileName = fileName


class NotSupported(ExpressionNode):
    """An expression node representing a subexpression that is not
    currently supported by the parser."""

    __slots__ = ()


class Uri(ExpressionNode):
    """An expression node representing a URI reference."""

    __slots__ = ('uri')

    def __init__(self, uriVal):
        super(Uri, self).__init__()

        if isinstance(uriVal, uri.Uri):
            self.uri = uriVal
        else:
            self.uri = uri.Uri(uriVal)

    def copyNode(self):
        return self.__class__(self.uri)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.uri)


class QName(LocationNode):
    """An expression node representing a qualified name."""

    __slots__ = ('qname')

    def __init__(self, qname, line=None, column=None, fileName=None):
        super(QName, self).__init__(line, column, fileName)

        self.qname = qname 

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.qname)
        

class Literal(ExpressionNode):
    """An expression node representing a RDF literal."""

    __slots__ = ('literal')

    def __init__(self, literalVal):
        super(Literal, self).__init__()

        if isinstance(literalVal, literal.Literal):
            self.literal = literalVal
        else:
            self.literal = literal.Literal(literalVal)

    def copyNode(self):
        return self.__class__(self.literal)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.literal)


class Var(LocationNode):
    """An expression node representing a SerQL variable by name."""

    __slots = ('name')

    def __init__(self, name, line=None, column=None, fileName=None):
        super(Var, self).__init__(line, column, fileName)

        self.name = name

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.name)


class FieldRef(ExpressionNode):
    """A reference to one particular field of a relation tuple."""

    __slots__ = ('relName',
                 'incarnation',
                 'fieldId')

    def __init__(self, relName, incarnation, fieldId):
        super(FieldRef, self).__init__()

        self.relName = relName
        self.incarnation = incarnation
        self.fieldId = fieldId

    def __repr__(self):
        return "%s_%d['%s']" % (self.relName,
                                self.incarnation,
                                self.fieldId)

    def copyNode(self):
        return self.__class__(self.relName, self.incarnation, self.fieldId)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % str(self))


class StatementPattern(ExpressionNode):
    """An expression node representing an statement pattern."""


    __slots__ = ()

    def __init__(self, subj, pred, obj):
        super(StatementPattern, self).__init__(subj, pred, obj)

    def copyNode(self, subj, pred, obj):
        return self.__class__(subj, pred, obj)


class Operation(ExpressionNode):
    """A node representing an operation."""

    __slots__ = ()


class UnaryOperation(Operation):
    """A node representing a unary operation."""

    __slots__ = ()

    def __init__(self, operand):
        super(UnaryOperation, self).__init__(operand)

    def copyNode(self, operand):
        return self.__class__(operand)


class BinaryOperation(Operation):
    """A node representing a binary operation."""

    __slots__ = ()

    def __init__(self, operand1, operand2):
        super(BinaryOperation, self).__init__(operand1, operand2)

    def copyNode(self, operand1, operand2):
        return self.__class__(operand1, operand2)


class Comparison(Operation):
    """A node representing a value comparison."""

    __slots__ = ()


class Equal(Comparison):
    """Determine if two or more operands are equal.""" 

    __slots__ = ()


class LessThan(Comparison, BinaryOperation):
    """Determine if operand1 < operand2.""" 

    __slots__ = ()


class LessThanOrEqual(Comparison, BinaryOperation):
    """Determine if operand1 <= operand2.""" 

    __slots__ = ()


class GreaterThan(Comparison, BinaryOperation):
    """Determine if operand1 > operand2.""" 

    __slots__ = ()


class GreaterThanOrEqual(Comparison, BinaryOperation):
    """Determine if operand1 >= operand2.""" 

    __slots__ = ()


class Different(Comparison):
    """Determine if two or more operands are different from each other.""" 

    __slots__ = ()


class BooleanOperation(Operation):
    """A node representing a boolean operation."""

    __slots__ = ()


class Or(BooleanOperation):
    """A boolean 'or' operation."""

    __slots__ = ()


class And(BooleanOperation):
    """A boolean 'and' operation."""

    __slots__ = ()


class Not(BooleanOperation, UnaryOperation):
    """A boolean 'not' operation."""

    __slots__ = ()


class Relation(ExpressionNode):
    """An incarnation of a given relation."""

    __slots__ = ('name',
                 'incarnation')

    def __init__(self, name, incarnation):
        super(Relation, self).__init__()

        self.name = name
        self.incarnation = incarnation

    def copyNode(self):
        return self.__class__(self.name, self.incarnation)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s_%d' % (self.name, self.incarnation))


class Optional(ExpressionNode):
    """A node representing an optional relation."""

    __slots__ = ()

    def __init__(self, baseRel):
        super(Optional, self).__init__(baseRel)

    def copyNode(self, baseRel):
        return self.__class__(baseRel)


class Product(ExpressionNode):
    """A node representing a cartesian product of two or more
    relations."""

    __slots__ = ()

    def __init__(self, *relations):
        super(Product, self).__init__(*relations)


class Select(ExpressionNode):
    """A node representing an optional relation."""

    __slots__ = ()

    def __init__(self, rel, predicate):
        super(Select, self).__init__(rel, predicate)

    def copyNode(self, rel, predicate):
        return self.__class__(rel, predicate)


class MapResult(ExpressionNode):
    """Specify the column names of a result table, together with the
    relation incarnations they are bound to."""

    __slots__ = ('columnNames')

    def __init__(self, columnNames, rel, *mappingExprs):
        super(MapResult, self).__init__(rel, *mappingExprs)

        self.columnNames = columnNames

    def copyNode(self, rel, *mappingExprs):
        return self.__class__(self.columnNames, rel, *mappingExprs)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' [%s]' % ', '.join(self.columnNames))
