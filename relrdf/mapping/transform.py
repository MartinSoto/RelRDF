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


import re

from relrdf.commonns import xsd, rdf, rdfs, relrdf
from relrdf.expression import nodes
from relrdf.expression import rewrite
from relrdf.expression import literal, uri

from relrdf.typecheck.typeexpr import resourceType

import sqlnodes

class StatementResultTransformer(rewrite.ExpressionTransformer):
    """Transforms StatementResult into MapResult."""

    __slots__ = ()

    def StatementResult(self, expr, relExpr, *stmtTmpls):
        expr = nodes.MapResult([], relExpr)
        for i, stmtTmpl in enumerate(stmtTmpls):
            for colName, mappingExpr in zip(('subject', 'predicate', 'object'),
                                            stmtTmpl):
                expr.columnNames.append('%s%d' % (colName, i + 1))
                expr.append(mappingExpr)
        return expr

class ExplicitTypeTransformer(rewrite.ExpressionTransformer):
    """Add explicit columns to all MapResult subexpressions
    corresponding to the dynamic data type of each one of the
    original columns."""

    __slots__ = ()

    def MapResult(self, expr, relExpr, *mappingExprs):
        expr[0] = relExpr
        for i, mappingExpr in enumerate(mappingExprs):
            expr.columnNames[i*2+1:i*2+1] = 'type__' + expr.columnNames[i*2],
            expr[i*2+2:i*2+2] = nodes.DynType(expr[i*2+1].copy()),
            expr[i*2+1] = mappingExpr
        return expr

    def StatementResult(self, expr, relExpr, *stmtTmpls):
        expr = nodes.MapResult([], relExpr)
        for i, stmtTmpl in enumerate(stmtTmpls):
            for colName, mappingExpr in zip(('subject', 'predicate', 'object'),
                                            stmtTmpl):
                expr.columnNames.append('%s%d' % (colName, i + 1))
                expr.append(mappingExpr)

                expr.columnNames.append('type__%s%d' % (colName, i + 1))
                expr.append(nodes.DynType(mappingExpr.copy()))
        return expr

    def _setOperation(self, expr, *operands):
        expr.columnNames = list(operands[0].columnNames)
        expr[:] = operands
        return expr

    Union = _setOperation
    SetDifference = _setOperation
    Intersection = _setOperation


class ResultMappingTransformer(rewrite.ExpressionTransformer):
    """Applies a function to all result value columns."""

    __slots__ = ('function',)

    def __init__(self, function):
        super(ResultMappingTransformer, self).__init__()

        self.function = function

    def _applyFunction(self, expr):
        f = self.function.copy();
        f.append(expr.copy())
        return f

    def MapResult(self, expr, relExpr, *mappingExprs):
        expr[0] = relExpr
        for i, mappingExpr in enumerate(mappingExprs):
            expr[i+1] = self._applyFunction(mappingExprs[i])
        return expr

    def StatementResult(self, expr, relExpr, *stmtTmpls):
        expr = nodes.MapResult([], relExpr)
        for i, stmtTmpl in enumerate(stmtTmpls):
            for colName, mappingExpr in zip(('subject', 'predicate', 'object'),
                                            stmtTmpl):
                expr.columnNames.append('%s%d' % (colName, i + 1))
                expr.append(self._applyFunction(mappingExpr))

        return expr

    def _setOperation(self, expr, *operands):
        expr.columnNames = list(operands[0].columnNames)
        expr[:] = operands
        return expr

    Union = _setOperation
    SetDifference = _setOperation
    Intersection = _setOperation

class Incarnator(object):
    """A singleton used to generate unique relation incarnations."""

    __slots__ = ()

    currentIncarnation = 1

    @classmethod
    def makeIncarnation(cls):
        cls.currentIncarnation += 1
        return cls.currentIncarnation

    @classmethod
    def reincarnate(cls, *exprs):
        """Replaces the incarnations present in a set of expression by
        fresh incarnations. The purpose is to obtain new incarnations
        of complete sets of expressions, that are equivalent to, but
        independent from the originals.

        Returns a list of copied and reincarnated expressions."""

        # A dictionary of equivalences between old and new
        # incarnations.
        equiv = {}

        def postOp(expr, subexprsModif):
            if hasattr(expr, 'incarnation'):
                try:
                    newIncr = equiv[expr.incarnation]
                except KeyError:
                    newIncr = cls.makeIncarnation()
                    equiv[expr.incarnation] = newIncr

                expr.incarnation = newIncr

                return expr, True
            else:
                return expr, subexprsModif

        ret = []
        for expr in exprs:
            ret.append(rewrite.exprApply(expr.copy(), postOp=postOp)[0])

        return ret

class PureRelationalTransformer(rewrite.ExpressionTransformer):
    """An abstract expression transformer that transforms a decoupled
    expression containing patterns into a pure relational expression.
    """

    __slots__ = ('varBindings',)

    def __init__(self):
        super(PureRelationalTransformer, self).__init__(prePrefix='pre')

        # A dictionary for variable replacements. Variable names are
        # associated to value replacement expressions.
        self.varBindings = {}

    def matchPattern(self, pattern, replacementExpr, columnNames):
        """Match a pattern with a replacement expression and return a
        patern-free relational expression that delivers the values the
        pattern would deliver. Additionally, bind variables to
        appropriate expressions so that they can be substituted.

        `pattern`: The expression to be interpreted as a pattern. Its
        subexpressions should be either variables, or expressions
        delivering constant values.

        `replacementExpr`: A relational expression, corresponding to
        all possible values the pattern could produce, i.e., if the
        pattern would be used with different variables as
        subexpressions, it would produce exactly the value produced by
        replacementExpr.

        `columnNames`: An iterable containing the column names to be
        matched with the pattern's subexpressions."""

        # FIXME: Lift this restriction.
        assert isinstance(replacementExpr, nodes.MapResult)

        # Reincarnate the replacement expression.
        (replacementExpr,) = Incarnator.reincarnate(replacementExpr)

        coreExpr = replacementExpr[0]

        # Bind the variables and/or create the matching conditions.
        conds = []
        for component, columnName in zip(pattern, columnNames):
            valueExpr = replacementExpr.subexprByName(columnName)

            # Must be supplied by derived classes
            if isinstance(component, nodes.DefaultGraph):
                component = self._getDefaultGraph()

            if isinstance(component, nodes.Var):
                self.varBindings[component.name] = valueExpr
            else:
                conds.append(nodes.Equal(component, valueExpr))

        if conds == []:
            return coreExpr
        else:
            # Restrict the core expression with the conditions.
            return nodes.Select(coreExpr, nodes.And(*conds))


    def preSelect(self, expr):
        # Process the relation subexpression before the condition.
        expr[0] = self.process(expr[0])
        expr[1] = self.process(expr[1])
        return expr

    def preMapResult(self, expr):
        # Process the relation subexpression before the mapping
        # subexpressions.
        expr[0] = self.process(expr[0])
        expr[1:] = [self.process(mappingExpr)
                    for mappingExpr in expr[1:]]

        return expr

    def Var(self, expr):
        # Substitute the variable.
        return self.varBindings[expr.name].copy()

    def preStatementPattern(self, expr):
        # Don't process the subexpressions.
        return expr

    def StatementPattern(self, expr, context, subject, pred, object):
        return self.matchPattern(expr, *self.replStatementPattern(expr))

    def preReifStmtPattern(self, expr):
        # Don't process the subexpressions.
        return expr

    def Type(self, expr):
        repl = self.mapTypeExpr(expr.typeExpr)
        if repl is not None:
            return repl
        else:
            if hasattr(expr, 'id'):
                assert False, "Cannot determine type from [[%s]]" % expr.id
            else:
                assert False, "Cannot determine type"


class MatchReifTransformer(PureRelationalTransformer):
    """A `PureRelationalTransformer` extension to match reified
    statement patterns to custom replacement expressions."""

    __slots__ = ()

    def ReifStmtPattern(self, expr, context, stmt, subject, pred, object):
        return self.matchPattern(expr, *self.replReifStmtPattern(expr))


class StandardReifTransformer(PureRelationalTransformer):
    """A `PureRelationalTransformer` extension to convert reified
    statement patterns into the four standard equivalent statement
    patterns."""

    __slots__ = ()

    @staticmethod
    def makeUriNode(uri):
        uriNode = nodes.Uri(uri)
        uriNode.staticType = resourceType
        return uriNode

    def ReifStmtPattern(self, expr,  context, stmt, subject, pred, object):
        # Express in terms of normal patterns.
        pattern1 = nodes.StatementPattern(context.copy(),
                                          stmt.copy(),
                                          self.makeUriNode(rdf.type),
                                          self.makeUriNode(rdf.Statement))
        pattern2 = nodes.StatementPattern(context.copy(),
                                          stmt.copy(),
                                          self.makeUriNode(rdf.subject),
                                          subject)
        pattern3 = nodes.StatementPattern(context.copy(),
                                          stmt.copy(),
                                          self.makeUriNode(rdf.predicate),
                                          pred)
        pattern4 = nodes.StatementPattern(context.copy(),
                                          stmt.copy(),
                                          self.makeUriNode(rdf.object),
                                          object)

        return nodes.Product(self.StatementPattern(pattern1, *pattern1),
                             self.StatementPattern(pattern2, *pattern2),
                             self.StatementPattern(pattern3, *pattern3),
                             self.StatementPattern(pattern4, *pattern4))

