<<<<<<< TREE

from relrdf import commonns
=======
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


>>>>>>> MERGE-SOURCE
from relrdf.expression import nodes, rewrite

from typeexpr import commonType, LiteralType, genericLiteralType, \
     BlankNodeType, blankNodeType, ResourceType, resourceType, RdfNodeType

class DynTypeTransl(rewrite.ExpressionTransformer):
    """An expression translator that replaces DynType node
    with known type information where possible"""

    __slots__ = ()

    def __init__(self):
        super(DynTypeTransl, self).__init__(prePrefix='pre')

    def preDynType(self, expr):
        return (self._dynTypeExpr(expr[0].copy()),)

    def DynType(self, expr, subexpr):
        return subexpr

    def _dynTypeExpr(self, expr):
        
        # Only replace type if the expression is failsafe
        result = None
        if expr.failSafe:
            result = nodes.Type(expr.staticType)
                
        if result is None:
            # This expression has a generic type whose dynamic form
            # must be resolved later by the mapper.
            #
            # FIXME: Consider using another node type here instead of
            # DynType (MapperDynType?)
            result = nodes.DynType(expr)
            
        result.staticType = resourceType
        return result

class TypeCheckTranslator(rewrite.ExpressionTransformer):
    """An expression transformer that adds needed type compatibility checks
    to an expression."""
    
    __slots__ = ('positive', 'negative')

    def __init__(self, positive, negative):
        super(TypeCheckTranslator, self).__init__(prePrefix='pre')
        
        # Which values of the expression are actually interesting?
        # (in some cases, we are only interested in "positive" result,
        #  so no addition check is needed to distinguish "false" and
        #  "error" expression results - we're essentially working with
        #  a three-state-logic here)
        self.positive = positive
        self.negative = negative
        
        # The semantics are as follows: Let P(a) and N(a) be predicates
        # that are true iff a is true, but give false (P) or true (N) in
        # case of "a" being errornous. Then, the following holds:
        #
        # P(!a) = !N(a)                N(!a) = !P(a)
        # P(a & b) = P(a) & P(b)       N(a & b) = N(a) & N(b)
        # P(a | b) = P(a) | P(b)       N(a | b) = N(a) | N(b)
        
                
    # Only special nodes are interested only in either positive or negative
    # results, so everything is interesting by default
    def preDefault(self, expr):
        
        # Save old state, both results are interesting for the subtree
        (positive, self.positive) = (self.positive, True)
        (negative, self.negative) = (self.negative, True)
        
        # Recurse
        result = self._recurse(expr)
        
        # Restore old state
        self.positive = positive
        self.negative = negative
        
        # Go on
        return result
    
    def preNot(self, expr):
        
        # Swap, recurse, swap back
        (self.positive, self.negative) = (self.negative, self.positive)
        result = self._recurse(expr)
        (self.positive, self.negative) = (self.negative, self.positive)

        # Continue
        return result
    
    # These don't need adjustments before recursion
    def preOr(self, expr):
        return self._recurse(expr)
    def preAnd(self, expr):
        return self._recurse(expr)
    
    # For expressions that are false for non-compatible operands
    def _addTypecheckP(self, expr, *sexpr):
                
        # Check can be skipped where difference between "false" and
        # "error" isn't intersting,
        if not self.negative:
            expr[:] = sexpr
            return expr
        
        # Only do dynamic type check if both arguments are some sort of RDF node
        common = commonType(*expr)
        if not isinstance(common, RdfNodeType):
            return expr        
        
        # Add type check
        subexprCopies = [e.copy() for e in expr];
        return nodes.Or(expr, nodes.Not(nodes.TypeCompatible(*subexprCopies)))
    
    # For expressions that are true for non-compatible operands
    def _addTypecheckN(self, expr, *sexpr):
        
        # Check can be skipped where difference between "true" and
        # "error" isn't intersting,
        if not self.positive:
            expr[:] = sexpr
            return expr
        
        # Only do dynamic type check if both arguments are some sort of RDF node
        common = commonType(*expr)
        if not isinstance(common, RdfNodeType):
            return expr
        
        # Add type check
        subexprCopies = [e.copy() for e in expr];
        return nodes.And(expr, nodes.TypeCompatible(*subexprCopies))
    
    # For expressions that can return anything for non-compatible operands
    def _addTypecheckB(self, expr, *sexpr):
        
        # Parts of the check can be skipped if only one case is interesting
        if not self.positive:
            return self._addTypecheckP(expr, sexpr)
        if not self.negative:
            return self._addTypecheckN(expr, sexpr)
                
        # Only do dynamic type check if both arguments are some sort of RDF node
        common = commonType(*expr)
        if not isinstance(common, RdfNodeType):
            return expr
                
        # Add both type checks (TODO: could use "expr XOr typecheck" instead)
        subexprCopies = [e.copy() for e in expr];
        subexprCopies2 = [e.copy() for e in expr];
        return nodes.And(nodes.Or(expr,
                                  nodes.Not(nodes.TypeCompatible(*subexprCopies))),
                         nodes.TypeCompatible(*subexprCopies2))

    # TODO: Only checking comparisons. Should be expanded in future.
    Equal = _addTypecheckP
    Different = _addTypecheckN
    
    LessThan = _addTypecheckB
    LessThanOrEqual = _addTypecheckB
    GreaterThan = _addTypecheckB
    GreaterThanOrEqual = _addTypecheckB
    
class SelectTypeCheckTransformer(rewrite.ExpressionTransformer):
    """An expression transformer that adds dynamic type checks to
    all select predicates."""

    def __init__(self):
        super(SelectTypeCheckTransformer, self).__init__(prePrefix='pre')
    
    def Select(self, expr, rel, pred):
        
        # Add type checks, only positive cases are interesting
        translator = TypeCheckTranslator(True, False);
        pred = translator.process(pred)
        
        return nodes.Select(rel, pred)        

# Replace DynType nodes where possible
def dynTypeTranslate(expr):
    dynTypeTrans = DynTypeTransl()
    return dynTypeTrans.process(expr)

# Insert type checks into predicates
def typeCheckTranslate(expr):
    typeCheckTrans = SelectTypeCheckTransformer()
    return typeCheckTrans.process(expr)
