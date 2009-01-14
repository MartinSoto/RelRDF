
from relrdf.expression import rewrite, nodes

import sqlnodes

class SqlBoolTranslator(rewrite.ExpressionTransformer):
    """Translates an expression resulting in a boolean RDF value into an expression
    returning the equivalent raw SQL boolean"""
    
    def __init__(self):
        super(SqlBoolTranslator, self).__init__(prePrefix='pre')

    # Recurse only for boolean operators
    def recurse(self, expr):
        return self._recurse(expr)
    
    preOr = recurse
    preAnd = recurse
    preNot = recurse
    
    def preDefault(self, expr):
        # Stop processing at unknown nodes
        return expr[:]
    
    # Convert to the raw SQL equivalents
    def Or(self, expr, *subexpr):
        return sqlnodes.SqlOr(*subexpr)
    def And(self, expr, *subexpr):
        return sqlnodes.SqlAnd(*subexpr)
    def Not(self, expr, *subexpr):
        return sqlnodes.SqlNot(*subexpr)
    
    def Equal(self, expr, *subexpr):
        return sqlnodes.SqlEqual(*subexpr)
    def LessThan(self, expr, *subexpr):
        return sqlnodes.SqlLessThan(*subexpr)
    def LessThanOrEqual(self, expr, *subexpr):
        return sqlnodes.SqlLessThanOrEqual(*subexpr)
    def GreaterThan(self, expr, *subexpr):
        return sqlnodes.SqlGreaterThan(*subexpr)
    def GreaterThanOrEqual(self, expr, *subexpr):
        return sqlnodes.SqlGreaterThanOrEqual(*subexpr)
    def Different(self, expr, *subexpr):
        return sqlnodes.SqlDifferent(*subexpr)
    def TypeCompatible(self, expr, *subexpr):
        return sqlnodes.SqlTypeCompatible(*subexpr)
    
    # Keep existing boolean SQL nodes
    def keep(self, expr, *sexpr):
        # (Note we didn't recurse in this case, see above)
        return expr

    SqlOr = keep
    SqlAnd = keep
    SqlNot = keep
    
    SqlEqual = keep
    SqlIn = keep
    SqlLessThan = keep
    SqlLessThanOrEqual = keep
    SqlGreaterThan = keep
    SqlGreaterThanOrEqual = keep
    SqlDifferent = keep
    SqlTypeCompatible = keep
    SqlInArray = keep
        
    # Cast unknown nodes to bool
    def Default(self, expr, *subexpr):
        # (Note we didn't recurse in this case, see above)
        assert(isinstance(expr, nodes.ValueNode));
        return sqlnodes.SqlCastBool(expr)

_sqlBoolTranslator = SqlBoolTranslator()

def translateToSqlBool(expr):
    return _sqlBoolTranslator.process(expr)

class SqlSelectBoolTranslator(rewrite.ExpressionTransformer):
    """ Translates the predicates of all Select nodes to nodes returning raw
    SQL boolean values """

    def __init__(self):
        super(SqlSelectBoolTranslator, self).__init__(prePrefix='pre')       
    
    def Select(self, expr, rel, pred):
        
        # Convert predicate
        pred = translateToSqlBool(pred)
        
        # Return node with modified predicate
        return nodes.Select(rel, pred)
                  
_sqlSelectBoolTranslator = SqlSelectBoolTranslator()

def translateSelectToSqlBool(expr):
    return _sqlSelectBoolTranslator.process(expr)
