from relrdf.localization import _
from relrdf import error
from relrdf.expression import nodes, rewrite, simplify, util
from relrdf.typecheck import typeexpr

import spqnodes


class Scope(dict):
    """A dictionary containing variable substitutions for a SPARQL
    scope, where a scope corresponds to the variables used in a given
    group pattern. A single variable may be bound to many variable
    substitutions across scopes.

    Scopes also contain an excluded variables set used to check for
    pattern well designedness (see documentation in this module for
    details.)"""

    __slots__ = ('excluded',)

    def __init__(self):
        super(Scope, self).__init__()

        # The set of excluded variables in this pattern. Excluded
        # variables are variables that are present in the optional
        # side of an optional pattern but not in its fixed side.
        self.excluded = set()

    def _badDesignedException(self, var):
        raise error.SemanticError(msg=_("Query is not well designed due "
                                        "to variable '%s'") % var.name,
                                  extents=var.getExtents())

    def createBinding(self, var):
        """Bind the variable `var` (a `nodes.Var` object) with a new
        variable, that will be created and returned by this
        method. The returned variable will have the same static type
        as `var`."""
        if var in self.excluded:
            self._badDesignedException(var)

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

    def closeScope(self, containing=None, optional=False):
        """Closes a scope, optionally merging it into its containing
        scope, given by parameter `containing`.

        Closing a scope comprises three main operations. The first one
        is checking that none of the excluded variables in this scope
        is bound in the containing scope. If it is, an
        `error.SemanticError` is raised. Excluded variables are
        also added to the containing's scope excluded set.

        The second operation consists of merging the scope into its
        containing scope by adding to the containing scope every
        variable in this scope not present in it with a single binding
        from the contained scope. This serves to guarantee that the
        bindings to the variables in the contained scope will be
        preserved. Additionally, if `optional` is `True`, such
        variables will also be added to the containing scope's
        excluded variable set.

        The third and final operation is building and returning the
        scope's binding condition. The binding condition of a scope is
        an expression stating that all bindings of every variable in
        that scope are equal, and that they are equal to at least one
        of the bindings in the containing scope for the same variable,
        if there are any. In cases where this condition is trivially
        true, this method returns `None`.

        The first two operations are not performed if `containing` is
        `None`.

        This method renders the closed scope unusable. After invoking
        it, the object must be discarded."""

        # Check excluded variables.
        if containing is not None:
            for var in self.excluded:
                if var in containing:
                    self._badDesignedException(var)
                else:
                    containing.excluded.add(var)

        subconds = nodes.And()
        for var, bindings in self.items():
            # Bindings are already a nodes.Equal expression.
            assert isinstance(bindings, nodes.Equal), var

            if containing is not None:
                try:
                    # Try to append a binding to the containing scope.
                    bindings.append(iter(containing[var]).next(). \
                                    copy())
                except KeyError:
                    # If failed, enrich the contining scope with a
                    # binding to the local scope (it is actually the
                    # local scope that is binding the variable.)
                    containing[var] = nodes.Equal(bindings[0].copy())

                    if optional:
                        # This variable goes into the excluded set as
                        # well.
                        containing.excluded.add(var)

            if len(bindings) >= 2:
                subconds.append(bindings)

        expr = simplify.reduceUnary(subconds)
        return expr

    def variableRepl(self, var):
        """Returns one of the bindings for the variable `var` (a
        `nodes.Var` object). The returned binding is a fresh copy of
        the one stored in the symbol table."""
        return iter(self[var]).next().copy()


class PatternDecoupler(rewrite.ExpressionTransformer):
    """An expression transformer that decouples the patterns in a
    expression.

    Decoupling the patterns means replacing variables so that no
    variable is mentioned in more than one pattern position. Explicit
    conditions are added to preserve query semantics.

    This transformer also checks that all patterns in the query are
    well designed, in accordance to the definition by Perez, Arenas,
    and Gutierrez (arXiv:cs 0605124). This definition basically states
    that variables occurring in the optional side of an optional
    pattern, either must be used in its fixed side, or cannot be used
    anywhere else in the whole query.
    """

    __slots__ = ('currentScope',)

    def __init__(self):
        super(PatternDecoupler, self).__init__(prePrefix='pre')

    def _processResult(self, expr):
        # Create a separate scope for the expression.
        self.currentScope = Scope()

        # Process the relation subexpression first.
        expr[0] = self.process(expr[0])

        # Now process the mapping expressions/statement templates.
        expr[1:] = [self.process(mappingExpr)
                    for mappingExpr in expr[1:]]

        # Add the binding condition if necessary.
        cond = self.currentScope.closeScope()
        if cond != None:
            expr[0] = nodes.Select(expr[0], cond)

        return expr

    preMapResult = _processResult
    preStatementResult = _processResult

    _patternOrder = {
        nodes.StatementPattern: 1,
        spqnodes.GraphPattern: 2,
        spqnodes.OpenUnion: 2,     # Same priority.
        spqnodes.Optional: 3,
        spqnodes.Filter: 4
        }

    @classmethod
    def _patternSortKey(cls, pattern):
        return cls._patternOrder[pattern.__class__]

    def preGraphPattern(self, expr, optional=False):
        # Subexpressions of a complex graph pattern must be processed
        # in a particular order to make sure that variables are
        # visible exactly where they should be. We first sort the
        # subexpressions according to that order.
        expr.sort(key=self._patternSortKey)

        # Open a new scope.
        containing = self.currentScope
        self.currentScope = Scope()

        # Process the ordered subexpressions recursively.
        for i, subexpr in enumerate(expr):
            expr[i] = self.process(subexpr)

        # Add a filter with the binding condition.
        cond = self.currentScope.closeScope(containing, optional)
        if cond is not None:
            expr.append(spqnodes.Filter(cond))
        self.currentScope = containing

        return expr

    def GraphPattern(self, expr, *subexprs):
        # Process everything except optional patterns and filters.
        i = 0
        for subexpr in subexprs:
            if isinstance(subexpr, spqnodes.Optional) or \
               isinstance(subexpr, spqnodes.Filter):
                break
            i += 1

        expr = nodes.Product(*subexprs[:i])
        expr = simplify.reduceUnary(expr)
        assert expr is not None

        # Process optional patterns.
        for subexpr in subexprs[i:]:
            if isinstance(subexpr, spqnodes.Filter):
                break
            i += 1

            assert isinstance(subexpr, spqnodes.Optional)

            # Get rid of the soqnodes.Optional node.
            expr = nodes.LeftJoin(expr, subexpr[0])

        # Process filter expressions.
        filterExpr = nodes.And()
        for subexpr in subexprs[i:]:
            assert isinstance(subexpr, spqnodes.Filter)

            # Get rid of the spqnodes.Filter node.
            filterExpr.append(subexpr[0])
        filterExpr = simplify.reduceUnary(filterExpr)

        if filterExpr is not None:
            expr = nodes.Select(expr, filterExpr)

        return expr

    def preOptional(self, expr):
        assert isinstance(expr[0], spqnodes.GraphPattern)

        # Replace normal processing, calling the pre method with the
        # optional parameter set.
        expr[0] = self.GraphPattern(expr,
                                    *self.preGraphPattern(expr[0], True))

        return expr

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
            repl = nodes.Null()
            repl.staticType = typeexpr.nullType
            return repl


