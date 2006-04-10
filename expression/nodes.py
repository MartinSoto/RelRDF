import sys

import uri
import literal


class NodeExtents(object):
    """The extents of a node (with subnodes) in the source code."""

    __slots__ = ('fileName',
                 'startLine',
                 'startColumn',
                 'endLine',
                 'endColumn')

    def __init__(self):
        super(NodeExtents, self).__init__()

        self.fileName = None
        self.startLine = None
        self.startColumn = None
        self.endLine = None
        self.endColumn = None

    def setStartFromToken(self, token, parser=None):
        """Set the start fields of the extents object to the start of
        the provided token, and use the file name from the provided
        parser."""
        self.startLine = token.getLine()
        self.startColumn = token.getColumn()

        if parser is not None:
            self.fileName = parser.getFilename()

    def setEndFromToken(self, token):
        """Set the end fields of the extents object to the end of
        the provided token."""
        self.endLine = token.getLine()
        self.endColumn = token.getColumn() + len(token.getText())

    def setFromToken(self, token, parser=None):
        """Set the fields of the extents object to the extents of
        the provided token, and use the file name from the provided
        parser."""
        self.setStartFromToken(token, parser)
        self.setEndFromToken(token)

    def prettyPrint(self, stream=None):
        if stream == None:
            stream = sys.stdout

        stream.write("%s: %s.%s - %s.%s" % (self.fileName,
                                            self.startLine,
                                            self.startColumn,
                                            self.endLine,
                                            self.endColumn))


class ExpressionNode(list):
    """A node in a expression tree."""

    __slots__ = ('extents',
                 'startSubexpr',
                 'endSubexpr',

                 'staticType',
                 'dynamicType')

    def __init__(self, *subexprs):
        super(ExpressionNode, self).__init__(subexprs)
        assert self._checkSubexprs()

        # Explicit node extents. If None, extents are calculated based
        # on the subexpressions.
        self.extents = None

        # Start and end subexpressions for extent calculation. If
        # startSubexpr is None, the first subexpression will be
        # used. If endSubexpr is None, the last subexpression will be
        # used.
        self.startSubexpr = None
        self.endSubexpr = None

        # Static type of the expression, e.g., the most specific type
        # that can be determined for an expression at translation
        # time. If None, no type checking has been performed on the
        # expression.
        self.staticType = None

        # Dynamic type of the expression, a second expression telling
        # how to calculate the type in run-time, when the static type
        # is too generic. If the dynamic type is None, it is always
        # equal to the static type (i.e., it is known at translation
        # time and doesn't have to be calculated dynamically at all.)
        self.dynamicType = None

    def _checkSubexprs(self):
        for i, subexpr in enumerate(self):
            assert isinstance(subexpr, ExpressionNode), \
                   "subexpression %d '%s' is not an ExpressionNode" % \
                   (i, subexpr)

        return True

    def checkTree(self):
        """Check the expression to guarantee that it is a tree."""
        self._recursiveCheckTree(set())

    def _recursiveCheckTree(self, nodeSet):
        if id(self) in nodeSet:
            assert False, 'Node %d multiply referenced' % id(self)
        nodeSet.add(id(self))
        for subexpr in self:
            subexpr._recursiveCheckTree(nodeSet)

    def _getExplicitExtents(self):
        if self.extents == None:
            self.extents = NodeExtents()
        return self.extents

    def setExtents(self, extents):
        """Set `self`'s extents to `extents`."""
        self.extents = extents

    def setExtentsStartFromToken(self, token, parser=None):
        """Set the start fields of `self`'s extents to the start of
        the provided token, and use the file name from the provided
        parser."""
        extents = self._getExplicitExtents()
        extents.setStartFromToken(token, parser)

    def setExtentsEndFromToken(self, token):
        """Set the end fields of `self`'s extents to the end of the
        provided token."""
        extents = self._getExplicitExtents()
        extents.setEndFromToken(token)

    def setExtentsFromToken(self, token, parser=None):
        """Set `self`'s extents to the extents of the provided token,
        and use the file name from the provided parser."""
        extents = self._getExplicitExtents()
        extents.setFromToken(token, parser)

    def setStartSubexpr(self, subexpr):
        """Set `subexpr`as the start subexpression for extent
        calculation. This means that this node's extents will start
        where `subexpr` extents start."""
        self.startSubexpr = subexpr

    def setEndSubexpr(self, subexpr):
        """Set `subexpr`as the end subexpression for extent
        calculation. This means that this node's extents will end
        where `subexpr` extents ends."""
        self.endSubexpr = subexpr

    def getExtents(self):
        """Return a NodeExtents object with the extents of the current
        node (including its subnodes.)"""
        expl = self._getExplicitExtents()
        res = NodeExtents()

        if expl.startLine is not None:
            startExtents = expl
        elif self.startSubexpr is not None:
            startExtents = self.startSubexpr.getExtents()
        elif len(self) > 0:
            startExtents = self[0].getExtents()
        else:
            startExtents = None

        if startExtents is not None:
            res.startLine = startExtents.startLine
            res.startColumn = startExtents.startColumn
            res.fileName = startExtents.fileName            

        if expl.endLine is not None:
            endExtents = expl
        elif self.endSubexpr is not None:
            endExtents = self.endSubexpr.getExtents()
        elif len(self) > 0:
            endExtents = self[-1].getExtents()
        else:
            endExtents = None

        if endExtents is not None:
            res.endLine = endExtents.endLine
            res.endColumn = endExtents.endColumn

        return res

    def __repr__(self):
        attribs = self.attributesRepr()
        subexprs = ', '.join([repr(subexpr) for subexpr in self])

        if attribs != '' and subexprs != '':
            return "%s(%s, %s)" % (self.__class__.__name__,
                                   attribs, subexprs)
        elif attribs != '':
            return "%s(%s)" % (self.__class__.__name__, attribs)
        else:
            return "%s(%s)" % (self.__class__.__name__, subexprs)

    def attributesRepr(self):
        return ''

    def prettyPrint(self, stream=None, indentLevel=0):
        if stream == None:
            stream = sys.stdout

        stream.write("  " * indentLevel)

        #self.getExtents().prettyPrint(stream)
        #stream.write(": ")
        stream.write('[[%d]] ' % id(self))
        stream.write(self.__class__.__name__)

        self.prettyPrintAttributes(stream, indentLevel)

        if self.staticType is not None:
            stream.write(' st:<<%s>>' % self.staticType)
        if self.dynamicType is not None:
            stream.write(' dyn:<<%s>>' % self.dynamicType)

        stream.write('\n')
        for subexpr in self:
            subexpr.prettyPrint(stream, indentLevel + 1)

    def prettyPrintAttributes(self, stream, indentLevel):
        pass


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

    def attributesRepr(self):
        return repr(self.uri)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.uri)


class QName(ExpressionNode):
    """An expression node representing a qualified name."""

    __slots__ = ('qname')

    def __init__(self, qname):
        super(QName, self).__init__()

        self.qname = qname 

    def attributesRepr(self):
        return repr(self.qname)

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

    def attributesRepr(self):
        return repr(self.literal)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.literal)


class Var(ExpressionNode):
    """An expression node representing a SerQL variable by name."""

    __slots = ('name')

    def __init__(self, name):
        super(Var, self).__init__()

        self.name = name

    def attributesRepr(self):
        return repr(self.name)

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

    def attributesRepr(self):
        return '%s, %s, %s' % (repr(self.relName),
                               repr(self.incarnation),
                               repr(self.fieldId))

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.attributesRepr())


class StatementPattern(ExpressionNode):
    """An expression node representing an statement pattern."""

    __slots__ = ()

    def __init__(self, subj, pred, obj):
        super(StatementPattern, self).__init__(subj, pred, obj)


class ReifStmtPattern(ExpressionNode):
    """An expression node representing a reified statement pattern."""

    __slots__ = ()

    def __init__(self, var, subj, pred, obj):
        super(ReifStmtPattern, self).__init__(var, subj, pred, obj)


class Operation(ExpressionNode):
    """A node representing an operation."""

    __slots__ = ()


class UnaryOperation(Operation):
    """A node representing a unary operation."""

    __slots__ = ()

    def __init__(self, operand):
        super(UnaryOperation, self).__init__(operand)


class BinaryOperation(Operation):
    """A node representing a binary operation."""

    __slots__ = ()

    def __init__(self, operand1, operand2):
        super(BinaryOperation, self).__init__(operand1, operand2)


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

    def attributesRepr(self):
        return '%s, %s' % (repr(self.name), repr(self.incarnation))

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s_%d' % (self.name, self.incarnation))


class Optional(ExpressionNode):
    """A node representing an optional relation."""

    __slots__ = ()

    def __init__(self, baseRel):
        super(Optional, self).__init__(baseRel)


class Product(ExpressionNode):
    """A node representing a cartesian product of two or more
    relations."""

    __slots__ = ()

    def __init__(self, *relations):
        super(Product, self).__init__(*relations)


class Select(ExpressionNode):
    """A node representing a select expression."""

    __slots__ = ()

    def __init__(self, rel, predicate):
        super(Select, self).__init__(rel, predicate)


class MapResult(ExpressionNode):
    """Specify the column names of a result table, together with the
    expressions they are bound to."""

    __slots__ = ('columnNames',
                 'incarnation')

    def __init__(self, columnNames, rel, *mappingExprs):
        super(MapResult, self).__init__(rel, *mappingExprs)

        self.columnNames = columnNames

        # The incarnation can be used to give the resulting table a
        # name while generating SQL expressions.
        self.incarnation = None

    def _recursiveCheckTree(self, nodeSet):
        if id(self.columnNames) in nodeSet:
            assert False, 'Node %d multiply referenced' % id(self)
        nodeSet.add(id(self.columnNames))
        super(MapResult, self)._recursiveCheckTree(nodeSet)

    def attributesRepr(self):
        return repr(self.columnNames)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' [%s]' % ', '.join(self.columnNames))
        if self.incarnation is not None:
            stream.write(' _%d' % self.incarnation)


class SetOperation(Operation):
    """A generic set operation."""

    __slots__ = ('columnNames')

    def __init__(self, *subexprs):
        super(SetOperation, self).__init__(*subexprs)

        self.columnNames = []

    def attributesRepr(self):
        return repr(self.columnNames)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' [%s]' % ', '.join(self.columnNames))


class Union(SetOperation):
    """Set union operation."""

    __slots__ = ()


class SetDifference(SetOperation):
    """Set difference operation."""

    __slots__ = ()


class Intersection(SetOperation):
    """Set intersection operation."""

    __slots__ = ()


#
# Type Related Nodes
#

class DynType(UnaryOperation):
    """An expression node representing the dynamic type of an
    arbitrary expression. This is intended to be replaced by the
    database mapper. The replacement is an expression that produces an
    internal, runtime representation of the data type."""

    __slots = ()
