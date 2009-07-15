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


from relrdf.expression import rewrite, nodes

import sqlnodes

class SqlBoolTranslator(rewrite.ExpressionTransformer):
    """Translates an expression resulting in a boolean RDF value into
    an expression returning the equivalent raw SQL boolean."""
    
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
        
    # Cast unknown nodes to bool
    def Default(self, expr, *subexpr):
        # (Note we didn't recurse in this case, see above)
        assert(isinstance(expr, nodes.ValueNode));
        return sqlnodes.SqlCastBool(expr)


_sqlBoolTranslator = SqlBoolTranslator()

def translateToSqlBool(expr):
    return _sqlBoolTranslator.process(expr)


class SqlSelectBoolTranslator(rewrite.ExpressionTransformer):
    """ Translates the predicates of all Select and LeftJoin nodes to
    nodes returning raw SQL boolean values."""

    def __init__(self):
        super(SqlSelectBoolTranslator, self).__init__(prePrefix='pre')       
    
    def Select(self, expr, rel, pred):
        # Convert predicate
        expr[1] = translateToSqlBool(pred)

        return expr

    def LeftJoin(self, expr, fixed, optional, cond=None):
        if cond is not None:
            # Convert predicate.
            expr[2] = translateToSqlBool(cond)
        
        return expr

                  
_sqlSelectBoolTranslator = SqlSelectBoolTranslator()

def translateSelectToSqlBool(expr):
    return _sqlSelectBoolTranslator.process(expr)
