import re
import pprint

from commonns import rdf, relrdf
from expression import nodes
from expression import rewrite
from expression import uri


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
                 'currentIncarnation')

    RDF_TYPE = nodes.Uri(rdf.type)
    RDF_STATEMENT = nodes.Uri(rdf.Statement)
    RDF_SUBJECT = nodes.Uri(rdf.subject)
    RDF_PREDICATE = nodes.Uri(rdf.predicate)
    RDF_OBJECT = nodes.Uri(rdf.object)


    def __init__(self):
        self.currentIncarnation = 0

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

    def makeIncarnation(self):
        self.currentIncarnation += 1
        return self.currentIncarnation

    def mapPattern(self, subject, pred, object):
        incarnation = self.makeIncarnation()

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

    def mapReifPattern(self, var, subject, pred, object):
        return nodes.Product(self.mapPattern(var, self.RDF_TYPE,
                                             self.RDF_STATEMENT)[0],
                             self.mapPattern(var, self.RDF_SUBJECT,
                                             subject)[0],
                             self.mapPattern(var, self.RDF_PREDICATE,
                                             pred)[0],
                             self.mapPattern(var, self.RDF_OBJECT,
                                             object)[0]), True

    def mapExpression(self, expr):
        def preOp(expr):
            if isinstance(expr, nodes.MapResult):
                self.pushScope()
            return expr, False

        def postOp(expr, subexprsModif):
            if isinstance(expr, nodes.MapResult):
                # Close the scope and expand the variables.
                scope = self.popScope()
                expr, modif = scope.expandVariables(expr)

                # Add the binding condition if necessary.
                cond = scope.getCondition()
                if cond != None:
                    expr[0] = nodes.Select(expr[0], cond)
                    modif = True

                # Add an unique incarnation identifier.
                expr.incarnation = self.makeIncarnation()

                return expr, True
            elif isinstance(expr, nodes.StatementPattern):
                return self.mapPattern(*expr)
            elif isinstance(expr, nodes.ReifStmtPattern):
                return self.mapReifPattern(*expr)
            else:
                return expr, subexprsModif

        expr = rewrite.exprApply(expr, preOp=preOp, postOp=postOp)[0]
        return rewrite.simplify(expr)

    def prettyPrint(self, stream=None, indent=0):
        if stream == None:
            stream = sys.stdout


class VersionMapper(RelationalMapper):
    __slots__ = ('versionNumber')

    def __init__(self, versionNumber):
        super(VersionMapper, self).__init__()

        self.versionNumber = versionNumber

    def mapPattern(self, subject, pred, object):
        stmtIncr = self.makeIncarnation()
        verIncr = self.makeIncarnation()

        conds = []
        for id, node in (('subject', subject), ('predicate', pred),
                         ('object', object)):
            if isinstance(node, nodes.Var):
                self.currentScope().addBinding(node.name, 'statements',
                                               
                                               stmtIncr, id)
            else:
                ref = nodes.FieldRef('statements', stmtIncr, id)
                conds.append(nodes.Equal(ref, node))

        rel = nodes.Product(nodes.Relation('version_statement', verIncr),
                            nodes.Relation('statements', stmtIncr))

        conds.append(
            nodes.And(
                nodes.Equal(
                    nodes.FieldRef('version_statement', verIncr, 'version_id'),
                    nodes.Literal(self.versionNumber)),
                nodes.Equal(
                    nodes.FieldRef('version_statement', verIncr, 'stmt_id'),
                    nodes.FieldRef('statements', stmtIncr, 'id'))))

        return nodes.Select(rel, nodes.And(*conds)), True


class MultiVersionMapper(RelationalMapper):
    """
    <version> relrdf:contains <stmt>

    <version> := model:version_%d
    <stmt> := model:stmt_%d
    """

    __slots__ = ('baseNs')

    versionPattern = re.compile('version_([0-9]+)')
    stmtPattern = re.compile('stmt_([0-9]+)')


    def __init__(self, baseUri):
        super(MultiVersionMapper, self).__init__()

        self.baseNs = uri.Namespace(baseUri)

    def mapContainsRel(self, subject, object):
        verIncr = self.makeIncarnation()

        conds = []

        # 0 is never used as version or statement id.

        for col, pattern, node in (('version_id', self.versionPattern,
                                    subject),
                                   ('stmt_id', self.stmtPattern, object)):
            if isinstance(node, nodes.Uri):
                local = self.baseNs.getLocal(node.uri)
                if local is not None:
                    m = pattern.match(local)
                    if m is not None:
                        numId = int(m.group(1))
                    else:
                        numId = 0
                else:
                    numId = 0

                ref = nodes.FieldRef('version_statement', verIncr, col)
                conds.append(nodes.Equal(ref, nodes.Literal(numId)))
        else:
            self.currentScope().addBinding(node.name, 'version_statement',
                                           verIncr, col)

        rel = nodes.Relation('version_statement', verIncr)

        if len(conds) == 0:
            return rel, True
        else:
            return nodes.Select(rel, nodes.And(*conds)), True

    def mapPattern(self, subject, pred, object):
        if isinstance(pred, nodes.Uri):
            if pred.uri == relrdf.contains:
                return self.mapContainsRel(subject, object)

        stmtIncr = self.makeIncarnation()
        verIncr = self.makeIncarnation()

        conds = []
        for col, node in (('subject', subject), ('predicate', pred),
                          ('object', object)):
            if isinstance(node, nodes.Var):
                self.currentScope().addBinding(node.name, 'statements',
                                               stmtIncr, col)
            else:
                ref = nodes.FieldRef('statements', stmtIncr, col)
                conds.append(nodes.Equal(ref, node))

        rel = nodes.Product(nodes.Relation('not_versioned_statements',
                                           verIncr),
                            nodes.Relation('statements', stmtIncr))

        conds.append(
            nodes.Equal(
            nodes.FieldRef('not_versioned_statements', verIncr, 'stmt_id'),
            nodes.FieldRef('statements', stmtIncr, 'id')))

        return nodes.Select(rel, nodes.And(*conds)), True

    def mapReifPattern(self, var, subject, pred, object):
        stmtIncr = self.makeIncarnation()

        self.currentScope().addBinding(var.name, 'statements',
                                       stmtIncr, 'id')

        conds = []
        for col, node in (('subject', subject), ('predicate', pred),
                          ('object', object)):
            if isinstance(node, nodes.Var):
                self.currentScope().addBinding(node.name, 'statements',
                                               stmtIncr, col)
            else:
                ref = nodes.FieldRef('statements', stmtIncr, col)
                conds.append(nodes.Equal(ref, node))

        rel = nodes.Relation('statements', stmtIncr)

        if len(conds) == 0:
            return rel, True
        else:
            return nodes.Select(rel, nodes.And(*conds)), True
