from relrdf.expression import nodes
from relrdf.typecheck import typeexpr

import valueref

class SqlInt(nodes.ValueNode):
    """Represents a raw SQL integer"""
    
    __slots__ = ('val',)
    
    def __init__(self, val):
        self.val = val
        super(SqlInt, self).__init__()
        
class SqlEqual(nodes.Comparison):
    """Tests two values for equivalence, returning the result as a 
    raw SQL boolean value"""
    
    __slots__ = ()

class SqlIn(nodes.Comparison):
    """Tests wether a value appears in a value set (as returned by MapValue)"""
    
    __slots__ = ()

class SqlLessThan(nodes.Comparison):
    """Tests wether operand1 < operand2, returning the result as a
    raw SQL boolean value"""
    
    __slots__ = ()

class SqlLessThanOrEqual(nodes.Comparison):
    """Tests wether operand1 <= operand2, returning the result as a
    raw SQL boolean value"""
    
    __slots__ = ()

class SqlGreaterThan(nodes.Comparison):
    """Tests wether operand1 > operand2, returning the result as a
    raw SQL boolean value"""
    
    __slots__ = ()

class SqlGreaterThanOrEqual(nodes.Comparison):
    """Tests wether operand1 >= operand2, returning the result as a
    raw SQL boolean value"""
    
    __slots__ = ()

class SqlDifferent(nodes.Comparison):
    """Tests two values for equivalence, returning the negated result 
    as a raw SQL boolean value"""
    
    __slots__ = ()


class SqlTypeCompatible(nodes.Comparison):
    """Tests wether two values are type-compatible (comparable)"""
    
    __slots__ = ()

class SqlAnd(nodes.Comparison):
    """Calculcates the conjunction of two SQL boolean values"""

    __slots__ = ()

class SqlOr(nodes.Comparison):
    """Calculcates the disjunction of two SQL boolean values"""

    __slots__ = ()

class SqlNot(nodes.UnaryOperation):
    """Calculcates the negation of a SQL boolean values"""
    
    __slots__ = ()

class SqlCastBool(nodes.UnaryOperation):
    """Converts a RDF term value into an SQL bool (note this might fail
    if the term has the wrong type)"""
    
    __slots__ = ()

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

class SqlTypedFieldRef(SqlFieldRef):
    """Like SqlFieldRef, but points to a typed field (so this node
    is initialized with a valid type)."""
    
    def __init__(self, *args):
        super(SqlTypedFieldRef, self).__init__(*args)
        
        self.staticType = typeexpr.rdfNodeType

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

