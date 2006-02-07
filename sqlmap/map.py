import pprint

from expression import nodes
from expression import rewrite


class Scope(dict):
    """A dictionary containing the variable bindings of a single
    variable scope. A single variable may be bound to many relation
    columns."""

    __slots__ = ()

    def addBinding(self, varName, relName, incarnation, columnId):
        try:
            varBindings = self[varName]
        except KeyError:
            varBindings = []
            self[varName] = varBindings

        varBindings.append(nodes.FieldRef(relName, incarnation, columnId))

    def getCondition(self):
        subconds = []

        for binding in self.values():
            if len(binding) >= 2:
                subconds.append(nodes.Equal(*binding))

        if len(subconds) == 0:
            return None
        elif len(subconds) == 1:
            return subconds[0]
        else:
            return nodes.And(*subconds)

    def expandVariables(self, expr):
        def preOp(expr):
            # Select an arbitrary binding.
            return iter(self[expr.name]).next(), True

        return rewrite.exprMatchApply(expr, nodes.Var, preOp=preOp)

    def prettyPrint(self, stream=None, indent=0):
        if stream == None:
            stream = sys.stdout

        stream.write('Bindings:\n')
        pprint.pprint(self, stream, indent + 2)


class RelationalMapper(object):

    __slots__ = ('scopeStack',
                 'incarnations')
    
    def __init__(self):
        self.incarnations = {}

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

    def getIncarnation(self, relName):
        incarnation = self.incarnations.get(relName, 0) + 1
        self.incarnations[relName] = incarnation
        return incarnation

    def mapPattern(self, subject, pred, object):
        incarnation = self.getIncarnation('S')

        conds = []
        for id, node in (('subject', subject), ('predicate', pred),
                         ('object', object)):
            if isinstance(node, nodes.Var):
                self.currentScope().addBinding(node.name, 'S',
                                               incarnation, id)
            else:
                ref = nodes.FieldRef('S', incarnation, id)
                conds.append(nodes.Equal(ref, node))

        rel = nodes.Relation('S', incarnation)
        if conds == []:
            return rel, True
        else:
            return nodes.Select(rel, nodes.And(*conds)), True

    def mapExpression(self, expr):
        def preOp(expr):
            if isinstance(expr, nodes.MapResult):
                self.pushScope()
            return expr, False

        def postOp(expr, subexprsModif):
            if isinstance(expr, nodes.MapResult):
                return self.popScope().expandVariables(expr)
            elif isinstance(expr, nodes.StatementPattern):
                return self.mapPattern(*expr)
            else:
                return expr, subexprsModif

        expr = rewrite.exprApply(expr, preOp=preOp, postOp=postOp)[0]
        return rewrite.simplify(expr)

    def prettyPrint(self, stream=None, indent=0):
        if stream == None:
            stream = sys.stdout

        stream.write('Incarnations:\n')
        pprint.pprint(self.incarnations, stream, indent + 2)
