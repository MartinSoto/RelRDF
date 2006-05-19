import re
import pprint

from relrdf.commonns import xsd, rdf, relrdf
from relrdf.expression import nodes
from relrdf.expression import rewrite
from relrdf.expression import literal, uri

from relrdf.typecheck.typeexpr import resourceType

import sqlnodes


class ExplicitTypeTransformer(rewrite.ExpressionTransformer):
    """Add explicit columns to all MapResult subexpressions
    corresponding to tzhe dynamic data type of each one of the
    original columns."""

    __slots__ = ()

    def MapResult(self, expr, relExpr, *mappingExprs):
        expr[0] = relExpr
        for i, mappingExpr in enumerate(mappingExprs):
            expr.columnNames[i*2+1:i*2+1] = 'type__' + expr.columnNames[i*2],
            expr[i*2+2:i*2+2] = nodes.DynType(expr[i*2+1].copy()),
            expr[i*2+1] = mappingExpr
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


class Scope(dict):
    """A dictionary containing the variable bindings of a single
    variable scope. A single variable may be bound to many relation
    columns."""

    __slots__ = ()

    def addBinding(self, varName, valueExpr, dynTypeExpr):
        """Bind a variable name with a pair of expressions, one
        corresponding to its value and one corresponding to its
        dynamic type. Many bindings can be done for a single variable
        name."""
        try:
            varBindings = self[varName]
        except KeyError:
            varBindings = ([], [])
            self[varName] = varBindings

        varBindings[0].append(valueExpr)
        varBindings[1].append(dynTypeExpr)

    def getCondition(self):
        """Returns a condition expression, stating the fact that all
        bindings of a variable are equal."""
        subconds = []

        for valueExprs, dynTypeExprs in self.values():
            # Both lists should have the same lenght.
            if len(valueExprs) >= 2:
                subconds.append(nodes.And(nodes.Equal(*dynTypeExprs),
                                          nodes.Equal(*valueExprs)))

        if len(subconds) == 0:
            return None
        elif len(subconds) == 1:
            return subconds[0]
        else:
            return nodes.And(*subconds)

    def variableValue(self, var):
        try:
            # Select an arbitrary binding.
            return iter(self[var.name][0]).next()
        except KeyError:
            return var

    def variableDynType(self, var):
        try:
            # Select an arbitrary binding.
            return iter(self[var.name][1]).next()
        except KeyError:
            return var

    def prettyPrint(self, stream=None, indent=0):
        if stream == None:
            stream = sys.stdout

        stream.write('Bindings:\n')
        pprint.pprint(self, stream, indent + 2)


class PureRelationalTransformer(rewrite.ExpressionTransformer):
    """An abstract expression transformer that transforms an
    expression containing patterns into a pure relational expression."""

    __slots__ = ('scopeStack',)

    def __init__(self):
        super(PureRelationalTransformer, self).__init__(prePrefix='pre')

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


    def matchPattern(self, pattern, replacementExpr, columnNames):
        """Match a pattern with a replacement expression and produce a
        patern-free relational expression that delivers the values the
        pattern would deliver.

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
            dynTypeExpr = replacementExpr.subexprByName('type__' +
                                                        columnName)

            if isinstance(component, nodes.Var):
                self.currentScope().addBinding(component.name,
                                               valueExpr,
                                               dynTypeExpr)
            elif isinstance(component, nodes.Joker):
                pass
            else:
                conds.append(nodes.And(nodes.Equal(self.dynTypeExpr(component),
                                                   dynTypeExpr),
                                       nodes.Equal(component,
                                                   valueExpr)))

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

    def Var(self, expr):
        return self.currentScope().variableValue(expr).copy()

    def preStatementPattern(self, expr):
        # Don't process the subexpressions.
        return expr

    def StatementPattern(self, expr, context, subject, pred, object):
        return self.matchPattern(expr, *self.replStatementPattern(expr))

    def preReifStmtPattern(self, expr):
        # Don't process the subexpressions.
        return expr

    def preDynType(self, expr):
        return (self.dynTypeExpr(expr[0]),)

    def DynType(self, expr, subexpr):
        return subexpr


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

