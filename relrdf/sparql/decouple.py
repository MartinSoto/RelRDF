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


from relrdf.localization import _
from relrdf import error
from relrdf.expression import nodes, rewrite, simplify, util
from relrdf.typecheck import typeexpr

import spqnodes


class Scope(dict):
    """A dictionary containing variable substitutions for a SPARQL
    scope, where a scope corresponds to the variables used in a given
    group pattern. A single variable may be bound to many variable
    substitutions across scopes."""

    __slots__ = ()

    def __init__(self):
        super(Scope, self).__init__()

    def createBinding(self, var):
        """Bind the variable `var` (a `nodes.Var` object) with a new
        variable, that will be created and returned by this
        method. The returned variable will have the same static type
        as `var`."""
        try:
            varBindings = self[var]
        except KeyError:
            varBindings = nodes.Equal()
            self[var] = varBindings

        newVar = util.VarMaker.make()
        newVar.staticType = var.staticType

        varBindings.append(newVar)

        # Copy here so that we can build the condition using the
        # original object.
        return newVar.copy()

    def closeScope(self, containing=None):
        """Closes a scope, optionally merging it into its containing
        scope, given by parameter `containing`.

        Closing a scope comprises two main operations. The first one
        consists of merging the scope into its containing scope by
        adding to the containing scope every variable in this scope
        not present in it with a single binding from the contained
        scope. This serves to guarantee that the bindings to the
        variables in the contained scope will be preserved. This
        operation is not performed if `containing` is `None`.

        The second operation is building and returning the scope's
        binding condition. The binding condition of a scope is an
        expression stating that all bindings of every variable in that
        scope are equal, and that they are equal to at least one of
        the bindings in the containing scope for the same variable, if
        there are any. In cases where this condition is trivially
        true, this method returns `None`.

        This method renders the closed scope unusable. After invoking
        it, the closed scope must be discarded."""

        subconds = nodes.And()
        for var, bindings in self.items():
            # Bindings are already a nodes.Equal expression.
            assert isinstance(bindings, nodes.Equal), var

            if containing is not None:
                # Bind the variable in the containing scope to one of
                # the bindings in this scope.
                try:
                    contBindings = containing[var]
                except KeyError:
                    contBindings = nodes.Equal()
                    containing[var] = contBindings
                contBindings.append(bindings[0].copy())

            if len(bindings) >= 2:
                subconds.append(bindings)

        expr, m = simplify.reduceUnary(subconds)
        return expr

    def variableRepl(self, var):
        """Returns one of the bindings for the variable `var` (a
        `nodes.Var` object). The returned binding is a fresh copy of
        the one stored in the symbol table."""
        return iter(self[var]).next().copy()


class PatternDecoupler(rewrite.ExpressionTransformer):
    """An expression transformer that decouples the patterns in an
    expression.

    Decoupling the patterns means replacing variables so that no
    variable is mentioned in more than one pattern position. Explicit
    conditions are added to preserve query semantics.
    """

    __slots__ = ('currentScope',)

    def __init__(self):
        super(PatternDecoupler, self).__init__(prePrefix='pre')

        self.currentScope = None

    def _processResultOrModifier(self, expr):
        #  All result and modifier nodes have the same basic
        #  structure. The first subexpression is either a modifier or
        #  the main query expression. Other subexpressions, if any,
        #  are scalars that must be evaluated in the context of the
        #  main query expression.

        # Create a scope for the first subexpression.
        containing = self.currentScope
        self.currentScope = Scope()

        # Process the first subexpression first. Directly or
        # indirectly, this will process the main query expression.
        expr[0] = self.process(expr[0])

        # Process all other subexpressions in the same context.
        expr[1:] = [self.process(mappingExpr)
                    for mappingExpr in expr[1:]]

        # Close the scope into the containing scope, if any.
        cond = self.currentScope.closeScope(containing)
        self.currentScope = containing

        if cond != None:
            # Add the condition to the subexpression.
            expr[0] = nodes.Select(expr[0], cond)

        return expr

    preMapResult = _processResultOrModifier
    preStatementResult = _processResultOrModifier
    preDistinct = _processResultOrModifier
    preSort = _processResultOrModifier
    preOffsetLimit = _processResultOrModifier

    def preProject(self, expr):
        """Process a `nodes.Project` node.

        Similar nodes can also be processed, such as the result nodes."""
        # Create a scope for the expression.
        containing = self.currentScope
        self.currentScope = Scope()

        # Process the first subexpression first. Directly or
        # indirectly, this will process the main query expression.
        expr[0] = self.process(expr[0])

        # Process all other subexpressions in the same context.
        expr[1:] = [self.process(mappingExpr)
                    for mappingExpr in expr[1:]]

        # Close the scope into the containing scope, if any.
        cond = self.currentScope.closeScope(containing)
        self.currentScope = containing

        if cond != None:
            # Add the condition to the subexpression.
            expr[0] = nodes.Select(expr[0], cond)
        self.currentScope = containing

        if self.currentScope is not None:
            # This is a nested projection expression. It hides all
            # variables in its subexpressions from the containing
            # scope, but contributes variables corresponding to
            # its column names.
            for name in expr.columnNames:
                self.currentScope.createBinding(nodes.Var(name))

        return expr

    def preUnion(self, expr):
        assert isinstance(expr.staticType, typeexpr.RelationType)

        # In a union, a number of independent subexpressions produce
        # results that contribute to the same relation. In order to
        # decouple their variables, we encapsulate the subexpressions
        # in Project nodes that map their decoupled variables into the
        # same set of variables.

        # The union expression contributes a number of variables to
        # its containing scope. Make a list with them.
        origVars = [nodes.Var(colName)
                    for colName in expr.staticType.getColumnNames()]

        # These variables must bound in the containing scope. Bind
        # them and save the resulting names.
        resultColNames = [self.currentScope.createBinding(var).name
                          for var in origVars]

        # Prevent the subexpression processing from adding any further
        # variables to the containing scope.
        containing = self.currentScope
        self.currentScope = None

        for i, subexpr in enumerate(expr):
            # Encapsulate the subexpression in a Project node. This
            # node projects the original variables (as still present
            # in the subexpression) into the names for these variables
            # as bound in the containing scope.
            encapsulated = nodes.Project(list(resultColNames),
                                         subexpr,
                                         *[v.copy() for v in origVars])

            # Decouple the variables in this node.
            expr[i] = self.preProject(encapsulated)

        self.currentScope = containing

        return expr

    def Union(self, expr, *subexprs):
        expr.columnNames = list(subexprs[0].columnNames)
        return expr

    def preSelect(self, expr):
        # Open a new scope.
        containing = self.currentScope
        self.currentScope = Scope()

        # Process the relation subexpression (fills the scope).
        expr[0] = self.process(expr[0])

        # Process the condition.
        selectCond = self.process(expr[1])

        # Add the binding condition (if any).
        cond = self.currentScope.closeScope(containing)
        if cond is not None:
            selectCond = nodes.And(selectCond, cond)
        self.currentScope = containing

        expr[1] = selectCond

        return expr

    def preLeftJoin(self, expr):
        # Any binding conditions for the fixed (left operand) side of
        # the left join cannot be merged into the join condition,
        # because this would lead to spurious results. For this
        # reason, we need to create two scopes: One for the whole left
        # join (outer) and one for the fixed operand (inner).

        # Open the scopes.
        containing = self.currentScope
        outer = Scope()
        self.currentScope = Scope()

        # Process the fixed relation operand (this fills the inner
        # scope).
        expr[0] = self.process(expr[0])

        # Close the inner scope (into the outer scope).
        cond = self.currentScope.closeScope(outer)
        self.currentScope = outer

        # Merge the condition if necessary.
        if cond is not None:
            if isinstance(expr[0], nodes.Select):
                expr[0][1] = nodes.And(cond, expr[0][1])
            else:
                expr[0] = nodes.Select(expr[0], cond)

        # Process the optional part of the left join in the outer
        # scope. This makes variables in the fixed part visible to the
        # optional part.
        expr[1] = self.process(expr[1])

        # Process the left join condition (if any).
        if len(expr) == 3:
            expr[2] = self.process(expr[2])

        # Close the outer scope.
        cond = self.currentScope.closeScope(containing)
        self.currentScope = containing

        # Add the binding condition (if any) to the join condition.
        if cond is not None:
            if len(expr) == 2:
                expr.append(cond)
            else:
                expr[2] = nodes.And(expr[2], cond)

        return expr

    def Join(self, expr, *operands):
        # After decoupling, joins become pure Cartesian products.
        return nodes.Product(*operands)

    def preStatementPattern(self, expr):
        # Don't process the subexpressions.
        return expr

    def StatementPattern(self, expr, context, subject, pred, object):
        for i, subexpr in enumerate(expr):
            if isinstance(subexpr, nodes.Var):
                expr[i] = self.currentScope.createBinding(subexpr)

        return expr

    def Var(self, expr):
        try:
            return self.currentScope.variableRepl(expr)
        except KeyError:
            # We have an unbound variable. It can be replaced by a
            # null value right away.
            repl = nodes.Null()
            repl.staticType = typeexpr.nullType
            return repl
