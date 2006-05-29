from relrdf.expression import nodes, rewrite, simplify, util
from relrdf.typecheck import typeexpr

import spqnodes


class ScopeStack(list):
    """A stack of dictionaries containing variable substitutions for a
    number of SPARQL scopes. For the moment, there is a main scope
    scope for the whole query, and optional patterns introduce
    additional scopes. A single variable may be bound to many variable
    substitutions across scopes."""

    __slots__ = ()

    def __init__(self):
        super(ScopeStack, self).__init__()

    def openScope(self):
        """Open (create) a new scope on top of the scope stack."""
        self.append({})

    def currentScope(self):
        """Return the current (topmost) scope."""
        return self[-1]

    def createBinding(self, varName, nodeType=False):
        """Bind the variable with name `varName` with a new variable,
        that will be created and returned by this method. The created
        variable will get its static type set to
        `typeexpr.rdfNodeType` if `nodeType` is `True` and to
        `resourceType` otherwise.

        Many bindings can be done for a single variable name. Bindings
        in a scope get automatically bound to bindings in higher
        scopes."""
        try:
            varBindings = self.currentScope()[varName]
        except KeyError:
            # Look for the variable in previous scopes.
            prevBinding = None
            for scope in reversed(self[:-1]):
                try:
                    prevBinding = iter(scope[varName]).next().copy()
                    break
                except KeyError:
                    pass

            if prevBinding is not None:
                # Bind to previous scope.
                varBindings = [prevBinding]
            else:
                varBindings = []
            self.currentScope()[varName] = varBindings

        newVar = util.VarMaker.make()
        if nodeType:
            newVar.staticType = typeexpr.rdfNodeType
        else:
            newVar.staticType = typeexpr.resourceType

        varBindings.append(newVar)

        # Copy here so that we can build the condition using the
        # original object.
        return newVar.copy()

    def closeScope(self):
        """Closes (destroys) the topmost scope in the stack and
        returns its binding condition.

        The binding condition of a scope is an expression stating that
        all bindings of every variable in that scope are equal, and
        that they are equal to at least one of the bindings in
        previous scopes for the same variable, if there are any. In
        cases where this condition is trivially true, this method
        returns `None`."""
        subconds = []

        for bindings in self.currentScope().values():
            if len(bindings) >= 2:
                subconds.append(nodes.Equal(*bindings))

        if len(subconds) == 0:
            cond = None
        elif len(subconds) == 1:
            cond = subconds[0]
        else:
            cond = nodes.And(*subconds)

        self.pop()

        return cond

    def variableRepl(self, varName):
        """Returns one of the bindings for the variable with variable
        name `varName`."""
        return iter(self.currentScope()[varName]).next().copy()


class PatternDecoupler(rewrite.ExpressionTransformer):
    """An expression transformer that decouples the patterns in a
    expression.

    Decoupling the patterns means replacing variables so that no
    variable is mentioned in more than one pattern position. Explicit
    conditions are added to preserve query semantics.

    This transformer also decouples scopes, i.e., when a single
    variable name is used in different scopes it will be replaced by
    a different variable in each scope.
    """

    __slots__ = ('scopeStack',)

    def __init__(self):
        super(PatternDecoupler, self).__init__(prePrefix='pre')

        self.scopeStack = ScopeStack()

    def preMapResult(self, expr):
        # Create a separate scope for the expression.
        self.scopeStack.openScope()

        # Process the relation subexpression first.
        expr[0] = self.process(expr[0])

        # Now process the mapping expressions.
        expr[1:] = [self.process(mappingExpr)
                    for mappingExpr in expr[1:]]

        # Add the binding condition if necessary.
        cond = self.scopeStack.closeScope()
        if cond != None:
            expr[0] = nodes.Select(expr[0], cond)

        return expr

    def preGraphPattern(self, expr):
        # Subexpressions must be processed in a particular order:

        # First simple triple patterns...
        for i, subexpr in enumerate(expr):
            if isinstance(subexpr, nodes.StatementPattern):
                expr[i] = self.process(subexpr)

        # ...then, everything else except filters ...
        for i, subexpr in enumerate(expr):
            if not isinstance(subexpr, spqnodes.Filter) and \
               not isinstance(subexpr, nodes.StatementPattern) :
                expr[i] = self.process(subexpr)

        # ... and, filters finally.
        for i, subexpr in enumerate(expr):
            if isinstance(subexpr, spqnodes.Filter):
                expr[i] = self.process(subexpr)

        return expr

    def GraphPattern(self, expr, *subexprs):
        triplePatterns = nodes.Product()
        for subexpr in subexprs:
            if isinstance(subexpr, nodes.StatementPattern):
                triplePatterns.append(subexpr)
        expr = simplify.reduceUnary(triplePatterns)

        assert expr is not None

        filterExpr = nodes.And()
        for subexpr in subexprs:
            if isinstance(subexpr, spqnodes.Filter):
                # Get rid of the filter node.
                filterExpr.append(subexpr[0])
        filterExpr = simplify.reduceUnary(filterExpr)

        if filterExpr is not None:
            expr = nodes.Select(expr, filterExpr)

        return expr

    def preStatementPattern(self, expr):
        # Don't process the subexpressions.
        return expr

    def StatementPattern(self, expr, context, subject, pred, object):
        for i, subexpr in enumerate(expr):
            if isinstance(subexpr, nodes.Var):
                expr[i] = self.scopeStack.createBinding(subexpr.name,
                                                        i == 3)

        return expr

    def Var(self, expr):
        try:
            return self.scopeStack.variableRepl(expr.name).copy()
        except KeyError:
            return nodes.Null()

