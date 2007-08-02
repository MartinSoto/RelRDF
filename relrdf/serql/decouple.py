from relrdf.expression import nodes, rewrite, util
from relrdf.typecheck import typeexpr


class Scope(dict):
    """A dictionary containing variable substitutions for a single
    variable scope. A single variable may be bound to many variable
    substitutions."""

    __slots__ = ()

    def createBinding(self, varName, nodeType=False):
        """Bind the variable with name `varName` with a new variable,
        that will be created and returned by this method. The created
        variable will get its static type set to
        `typeexpr.rdfNodeType` if `nodeType` is `True` and to
        `typeexpr.resourceType` otherwise. Many bindings can be done
        for a single variable name."""
        try:
            varBindings = self[varName]
        except KeyError:
            varBindings = []
            self[varName] = varBindings

        newVar = util.VarMaker.make()
        if nodeType:
            newVar.staticType = typeexpr.rdfNodeType
        else:
            newVar.staticType = typeexpr.resourceType

        varBindings.append(newVar)

        # Copy here so that we can build the condition using the
        # original object.
        return newVar.copy()

    def getCondition(self):
        """Returns a condition expression stating the fact that all
        bindings of every variable in the scope are equal. In cases
        where this condition is trivially true, this method returns
        `None`.

        This method can be called only once for each scope."""
        subconds = []

        for bindings in self.values():
            if len(bindings) >= 2:
                subconds.append(nodes.Equal(*bindings))

        if len(subconds) == 0:
            return None
        elif len(subconds) == 1:
            return subconds[0]
        else:
            return nodes.And(*subconds)

    def variableRepl(self, varName):
        """Returns one of the bindings for the variable with variable
        name `varName`."""
        return iter(self[varName]).next().copy()


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

        # A stack of Scope objects, to handle nested variable
        # scopes.
        self.scopeStack = []

    def pushScope(self):
        """Push a new scope into the scope stack."""
        self.scopeStack.append(Scope())

    def popScope(self):
        """Pop the topmost scope form the scope stack and return
        it."""
        return self.scopeStack.pop()

    def currentScope(self):
        """Return the current (topmost) scope."""
        return self.scopeStack[-1]

    def preSelect(self, expr):
        # Process the relation subexpression before the condition.
        expr[0] = self.process(expr[0])
        expr[1] = self.process(expr[1])
        return expr

    def preMapResult(self, expr):
        # Create a separate scope for the expression.
        self.pushScope()

        # Process the relation subexpression first.
        expr[0] = self.process(expr[0])

        # Add the binding condition if necessary.
        cond = self.currentScope().getCondition()
        if cond != None:
            expr[0] = nodes.Select(expr[0], cond)

        # Now process the mapping expressions.
        expr[1:] = [self.process(mappingExpr)
                    for mappingExpr in expr[1:]]

        # Remove the scope.
        scope = self.popScope()

        return expr

    def preStatementPattern(self, expr):
        # Don't process the subexpressions.
        return expr

    def StatementPattern(self, expr, context, subject, pred, object):
        for i, subexpr in enumerate(expr):
            if isinstance(subexpr, nodes.Var):
                expr[i] = self.currentScope().createBinding(subexpr.name,
                                                            i == 3)

        return expr

    def preReifStmtPattern(self, expr):
        # Don't process the subexpressions.
        return expr

    def ReifStmtPattern(self, expr, context, stmt, subject, pred, object):
        for i, subexpr in enumerate(expr):
            if isinstance(subexpr, nodes.Var):
                expr[i] = self.currentScope().createBinding(subexpr.name,
                                                            i == 4)

        return expr

    def Var(self, expr):
        return self.currentScope().variableRepl(expr.name).copy()
