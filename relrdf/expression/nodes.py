import sys
import copy
import weakref

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

    def setEndFromToken(self, token, extraLength=0):
        """Set the end fields of the extents object to the end of the
        provided token. The value of `extraLength` will be added to
        the token text length. This is for cases where some text
        belonging to the token is supressed in the parser using the
        '!'  operator."""
        self.endLine = token.getLine()
        self.endColumn = token.getColumn() + len(token.getText()) + \
                         extraLength

    def setFromToken(self, token, parser=None, extraLength=0):
        """Set the fields of the extents object to the extents of the
        provided token, and use the file name from the provided
        parser. See `setEndFromToken` for the meaning of
        `extraLength`."""
        self.setStartFromToken(token, parser)
        self.setEndFromToken(token, extraLength=extraLength)

    def prettyPrint(self, stream=None):
        if stream == None:
            stream = sys.stdout

        stream.write("%s: %s.%s - %s.%s" % (self.fileName,
                                            self.startLine,
                                            self.startColumn,
                                            self.endLine,
                                            self.endColumn))


class BasicExpressionNode(list):
    """A node in a expression tree."""

    __slots__ = ('extents',
                 'startSubexpr',
                 'endSubexpr',

                 'staticType',
                 'dynamicType')

    def __init__(self, *subexprs):
        super(BasicExpressionNode, self).__init__(subexprs)

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

    def copy(self):
        """Return a copy of the complete expression tree."""
        return copy.deepcopy(self)


    #
    # Structural Checking
    #

    def getId(self):
        return id(self)

    def checkTree(self):
        """Check the expression to guarantee that it is a tree."""
        self._recursiveCheckTree(set())

    def _recursiveCheckTree(self, nodeSet):
        if self.getId() in nodeSet:
            assert False, 'Node %d multiply referenced' % self.getId()
        nodeSet.add(self.getId())
        for subexpr in self:
            subexpr._recursiveCheckTree(nodeSet)


    #
    # Extents
    #

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

    def setExtentsEndFromToken(self, token, extraLength=0):
        """Set the end fields of `self`'s extents to the end of the
        provided token. See `NodeExtents.setEndFromToken` for the
        meaning of `extraLength`."""
        extents = self._getExplicitExtents()
        extents.setEndFromToken(token, extraLength=extraLength)

    def setExtentsFromToken(self, token, parser=None, extraLength=0):
        """Set `self`'s extents to the extents of the provided token,
        and use the file name from the provided parser. See
        `NodeExtents.setEndFromToken` for the meaning of
        `extraLength`."""
        extents = self._getExplicitExtents()
        extents.setFromToken(token, parser, extraLength=extraLength)

    def setStartSubexpr(self, subexpr):
        """Set `subexpr` as the start subexpression for extent
        calculation. This means that this node's extents will start
        where `subexpr` extents start."""
        self.startSubexpr = subexpr

    def setEndSubexpr(self, subexpr):
        """Set `subexpr` as the end subexpression for extent
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


    #
    # Expression Tree Display
    #

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
        stream.write('[[%d]] ' % self.getId())
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


class ExclusiveExpressionNode(BasicExpressionNode):
    """A debugging extension of the basic expression node, intended to
    detect attempts at sharing subexpressions. It works by extending
    the basic list operations in such a way that subexpressions that
    were attached to a tree, get detached before being attached to a
    second tree, and their original location gets marked with a
    `Pruned` node."""

    __slots__ = ('id',

                 'parent',
                 '__weakref__')

    _idCounter = 1

    def __init__(self, *subexprs):
        # An explicit id for easier debugging.
        self.id = ExclusiveExpressionNode._idCounter
        ExclusiveExpressionNode._idCounter += 1

        # A weakref proxy object pointing to the parent expression
        # node, or `None`if this node is no subexpression of another
        # node.
        self.parent = None

        super(ExclusiveExpressionNode, self).__init__(*subexprs)
        self._addSubexprs(subexprs)

    def __deepcopy__(self, memoDict):
        # The basic copy.copy operation calls our own overwritten list
        # operations when copying the subexpressions, which means they
        # will be stolen from this object.
        cp = copy.copy(self)

        for i, subexpr in enumerate(self):
            # Restore the subexpression.
            assert isinstance(subexpr, Pruned)
            subexpr = subexpr.prunedExpr
            super(ExclusiveExpressionNode, self).__setitem__(i, subexpr)
            subexpr.parent = weakref.proxy(self)

            # Copy the subexpression.
            subexprCp = subexpr.copy()
            super(ExclusiveExpressionNode, cp).__setitem__(i, subexprCp)
            subexprCp.parent = weakref.proxy(cp)

        cp.id = ExclusiveExpressionNode._idCounter
        ExclusiveExpressionNode._idCounter += 1
        
        cp.parent = None

        return cp

    def getId(self):
        return self.id


    #
    # Basic List Operations
    #

    # Extend basic list operations to check parameters, and update the
    # parent references as necessary.

    def _setParent(self, parent):
        if parent is not None:
            newParent = weakref.proxy(parent)
        else:
            newParent = None

        if self.parent is not None:
            try:
                self.parent._pruneSubexpr(self)
            except ReferenceError:
                self.parent = None
        assert self.parent is None

        self.parent = newParent

    def _pruneSubexpr(self, subexpr):
        # FIXME: index should work here.
        for i, se in enumerate(self):
            if subexpr is se:
                pos = i

        # We need to be careful not to trigger a _setParent operation
        # on the subexpression, because that leads to a recursive
        # infinite loop.
        super(ExclusiveExpressionNode,
              self).__setitem__(pos, Pruned(subexpr))

        subexpr.parent = None

    def _addSubexprs(self, sequence):
        for expr in sequence:
            expr._setParent(self)

    def _removeSubexprs(self, sequence):
        for expr in sequence:
            expr._setParent(None)

    def __setitem__(self, i, x):
        if isinstance(i, slice):
            self._removeSubexprs(self[i])
            ret = super(ExclusiveExpressionNode,
                        self).__setitem__(i, x)
            self._addSubexprs(x)
        else:
            self._removeSubexprs((self[i],))
            ret = super(ExclusiveExpressionNode,
                        self).__setitem__(i, x)
            self._addSubexprs((x,))
        return ret

    def __setslice__(self, i, j, sequence):
        return self.__setitem__(slice(i, j), sequence)

    def __delitem__(self, i):
        if isinstance(i, slice):
            self._removeSubexprs(self[i])
        else:
            self._removeSubexprs(self[i:i+1])
        return super(ExclusiveExpressionNode, self).__delitem__(i)

    def __delslice__(self, i, j):
        return self.__delitem__(slice(i, j))

    def append(self, x):
        ret = super(ExclusiveExpressionNode, self).append(x)
        self._addSubexprs((x,))
        return ret

    def insert(self, i, x):
        ret = super(ExclusiveExpressionNode, self).insert(i, x)
        self._addSubexprs((x,))
        return ret

    def extend(self, sequence):
        ret = super(ExclusiveExpressionNode, self).extend(sequence)
        self._addSubexprs(sequence)
        return ret

    def pop(self, i=None):
        if i is None:
            self._removeSubexprs(self[-1:])
            return super(ExclusiveExpressionNode, self).pop()
        else:
            self._removeSubexprs(self[i:i+1])
            return super(ExclusiveExpressionNode, self).pop(i)

    def remove(self, x):
        i = self.index(x)
        self._removeSubexprs(self[x:x+1])
        return super(ExclusiveExpressionNode, self).remove(x)


#class ExpressionNode(BasicExpressionNode):
class ExpressionNode(ExclusiveExpressionNode):
    __slots__ = ()


class Pruned(ExpressionNode):
    """A special expression node used to mark 'pruned' subexpressions,
    i.e. subexpressions that were moved to another node and thus
    cannot remain as subexpressions of the current one."""

    __slots__ = ('prunedExpr',)

    def __init__(self, prunedExpr):
        super(Pruned, self).__init__()

        self.prunedExpr = prunedExpr

    def _recursiveCheckTree(self, nodeSet):
        assert False, 'Pruned branch'

    def prettyPrint(self, stream=None, indentLevel=0):
        super(Pruned, self).prettyPrint(stream, indentLevel)
        self.prunedExpr.prettyPrint(stream, indentLevel + 1)

class NotSupported(ExpressionNode):
    """An expression node representing a subexpression that is not
    currently supported by the parser."""

    __slots__ = ()

#
# Value Nodes
#

class ValueNode(ExpressionNode):
    """A node that can be evaluated to a single value"""
    
    __slots__ = ()


class Null(ValueNode):
    """An expression node representing a null value."""

    __slots__ = ('uri',)

    def __init__(self):
        super(Null, self).__init__()

class Int(ValueNode):
    """Represents a raw SQL integer"""
    
    __slots__ = ('val',)
    
    def __init__(self, val):
        self.val = val
        super(Int, self).__init__()

class Uri(ValueNode):
    """An expression node representing a URI reference."""

    __slots__ = ('uri',)

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


class QName(ValueNode):
    """An expression node representing a qualified name."""

    __slots__ = ('qname',)

    def __init__(self, qname):
        super(QName, self).__init__()

        self.qname = qname 

    def attributesRepr(self):
        return repr(self.qname)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.qname)
        

class Literal(ValueNode):
    """An expression node representing a RDF literal."""

    __slots__ = ('literal',)

    def __init__(self, literalVal):
        super(Literal, self).__init__()

        if isinstance(literalVal, literal.Literal):
            self.literal = literalVal
        else:
            self.literal = literal.Literal(literalVal)

    def attributesRepr(self):
        return repr(self.literal)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.literal.getCanonical())


class Var(ValueNode):
    """An expression node representing a SerQL variable by name."""

    __slots = ('name')

    def __init__(self, name):
        super(Var, self).__init__()

        self.name = name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

    def attributesRepr(self):
        return repr(self.name)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.name)

class BlankNode(Var):
    """An expression node representing an unspecified blank node"""
    
    def __init__(self, name):
        super(BlankNode, self).__init__(name)

class FunctionCall(ValueNode):
    """A function call."""

    __slots__ = ('functionName')

    def __init__(self, functionName, *params):
        self.functionName = functionName
        super(FunctionCall, self).__init__(*params)


class If(ValueNode):
    """A functional if expression.

    An 'if' expression selects among two expressions based on a
    condition. THe intended semantics are that onyl the selected
    expression is evaluated."""

    __slots__ = ()

    def __init__(self, cond, thenExpr, elseExpr):
        super(If, self).__init__(cond, thenExpr, elseExpr)

#
# Operations
#

class Operation(ValueNode):
    """A node representing an operation."""

    __slots__ = ()

class TypeCompatible(Operation):
    """Determine if two or more operands are type-compatible (= comparable)""" 

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
    """Determine if two or more operands are different from each other.

    The result is True if there are two operands that are different.""" 

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


class ArithmeticOperation(Operation):
    """A node representing an arithmetic operation."""

    __slots__ = ()


class Plus(ArithmeticOperation):
    """An arithmetic addition."""

    __slots__ = ()


class Minus(ArithmeticOperation, BinaryOperation):
    """An arithmetic subtraction."""

    __slots__ = ()

    
class UMinus(ArithmeticOperation, UnaryOperation):
    """An arithmetic unary minus."""

    __slots__ = ()

    
class Times(ArithmeticOperation):
    """An arithmetic multiplication."""

    __slots__ = ()

    
class DividedBy(ArithmeticOperation, BinaryOperation):
    """An arithmetic division."""

    __slots__ = ()

class IsBound(UnaryOperation):
    """Determines wether a variable is bound to a value"""
    
    __slots__ = ()

class CastBool(UnaryOperation):
     """Converts the given value to the boolean datatype"""
    
     __slots__ = ()
  
class CastDecimal(UnaryOperation):
     """Converts the given value to the decimal datatype"""
    
     __slots__ = ()
  
class CastInt(UnaryOperation):
     """Converts the given value to the integer datatype"""
    
     __slots__ = ()
  
class CastDateTime(UnaryOperation):
     """Converts the given value to the date/time datatype"""
    
     __slots__ = ()
  
class CastString(UnaryOperation):
     """Converts the given value to the string datatype"""
    
     __slots__ = ()
  
class MapValue(BinaryOperation):
    """Computes the value of a single expression concerning a relation"""
    
    __slots__ = ()

#
# Pattern Nodes
#
    
class StatementPattern(ExpressionNode):
    """An expression node representing an statement pattern."""

    __slots__ = ()

    def __init__(self, context, subj, pred, obj):
        super(StatementPattern, self).__init__(context, subj, pred, obj)


class ReifStmtPattern(ExpressionNode):
    """An expression node representing a reified statement pattern."""

    __slots__ = ()

    def __init__(self, context, stmt, subj, pred, obj):
        super(ReifStmtPattern, self).__init__(context, stmt, subj, pred, obj)


class Joker(ExpressionNode):
    """An expression node representing a joker, i.e., an open
    position in a pattern tha can be filled with everything."""

    __slots__ = ()

    def __init__(self):
        super(Joker, self).__init__()

#
# Relational Operations
#

class RelationNode(ExpressionNode):
    """An expression that evaluates to a set of triples"""
    
    __slots__ = ()

class Empty(RelationNode):
    """An expression node representing an empty relation, i.e., one
    containing no tuples."""

    __slots__ = ()

    def __init__(self):
        super(Empty, self).__init__()


class Optional(RelationNode):
    """A node representing an optional relation."""

    __slots__ = ()

    def __init__(self, baseRel):
        super(Optional, self).__init__(baseRel)


class Product(RelationNode):
    """A node representing a cartesian product of two or more
    relations."""

    __slots__ = ()

    def __init__(self, *relations):
        super(Product, self).__init__(*relations)


class LeftJoin(RelationNode):
    """A node representing a left outer join of two or more
    relations."""

    __slots__ = ()

    def __init__(self, fixed, optional):
        super(LeftJoin, self).__init__(fixed, optional)


class Select(RelationNode):
    """A node representing a select expression."""

    __slots__ = ()

    def __init__(self, rel, predicate):
        super(Select, self).__init__(rel, predicate)

#
# Query Results
#

class QueryResult(ExpressionNode):
    """A base class for all nodes representing query results.
    """

    __slots__ = ()


class MapResult(QueryResult):
    """Specify the column names of a result table, together with the
    expressions they are bound to."""

    __slots__ = ('columnNames',
                 'incarnation'
                 )

    def __init__(self, columnNames, rel, *mappingExprs):
        super(MapResult, self).__init__(rel, *mappingExprs)

        self.columnNames = columnNames

        # The incarnation can be used to give the resulting table a
        # name while generating SQL expressions.
        self.incarnation = None
        
    def subexprByName(self, columnName):
        """Return the subexpression bound a to a particular column name."""
        return self[self.columnNames.index(columnName) + 1]

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

class StatementResult(QueryResult):
    """Specify the statement templates used to produce the result of a
    transformation ('construct') query. The first child of this node
    is a relational expression. The subsequent children are statement
    patterns, potentially containing variables that are instantiated
    by the expression."""

    __slots__ = ()

    def __init__(self, rel, *stmtPatterns):
        super(StatementResult, self).__init__(rel, *stmtPatterns)


class StatementTemplate(ExpressionNode):
    """An expression node representing a result statement template."""

    __slots__ = ()

    def __init__(self, subj, pred, obj):
        super(StatementTemplate, self).__init__(subj, pred, obj)


#
# Result Modifiers
#

class QueryResultModifier(ExpressionNode):
    """A base class for all nodes working in query results."""
    
    __slots__ = ()

class Distinct(QueryResultModifier):
    """Specify that the results produced by the subexpression must be
    filtered to eliminate repeated rows."""

    __slots__ = ()
    
    def __init__(self, operand):
        super(Distinct, self).__init__(operand)    

class OffsetLimit(QueryResultModifier):
    """Selects some rows from the results based on their position in
    the result list"""
    
    __slots__ = ('limit',
                 'offset'
                 )
    
    def __init__(self, subexpr):
        
        # Position (from top) of the first row to be returned
        self.offset = None
        
        # Maximum count of rows to return
        self.limit = None
        
        super(ExpressionNode, self).__init__(subexpr)
        
class Sort(QueryResultModifier):
    """Sorts the result rows according to the second subexpression"""
    
    __slots__ = ('ascending',
                )
       
    def __init__(self, subexpr, orderBy):
        
        # Ascending sort order is the default
        self.ascending = 1
        
        super(Sort, self).__init__(subexpr, orderBy)        

#
# Model Modification Operations
#

class ModifOperation(ExpressionNode):
    """Base class for modification operations. The subexpression is a
    construct query that produces the set of statements to be inserted
    into or deleted from the model."""

    __slots__ = ('graphUri',)

    def __init__(self, graphUri, subexpr):
        super(ModifOperation, self).__init__(subexpr)
        self.graphUri = graphUri


class Insert(ModifOperation):
    """An insert operation."""

    __slots__ = ()


class Delete(ModifOperation):
    """A delete operation."""

    __slots__ = ()


#
# Set Operations
#

class SetOperation(Operation):
    """A generic set operation."""

    __slots__ = ('columnNames',)

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
    mapper. The replacement is an expression that produces an
    internal, runtime representation of the data type."""

    __slots = ()


class Type(ValueNode):
    """An expression node corresponding to the runtime representation
    of a concrete data type. This is intended to be replaced by the
    mapper. The replacement is a, most probably constant, expression
    that produces an internal, runtime representation of the data
    type."""

    __slots__ = ('typeExpr',)

    def __init__(self, typeExpr):
        super(Type, self).__init__()

        self.typeExpr = typeExpr

    def attributesRepr(self):
        return repr(self.typeExpr)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.typeExpr)
    