import re
import pprint

from commonns import xsd, rdf, relrdf
from expression import nodes
from expression import rewrite
from expression import literal, uri

from typecheck.typeexpr import LiteralType, BlankNodeType, ResourceType, \
     RdfNodeType, resourceType, rdfNodeType
import typecheck 


TYPE_ID_RESOURCE = literal.Literal(1)
TYPE_ID_BLANKNODE = literal.Literal(2)
TYPE_ID_LITERAL = literal.Literal(3)


def makeFieldRef(relation, incarnation, col):
    ref = nodes.FieldRef(relation, incarnation, col)
    if col == 'object':
        ref.staticType = rdfNodeType
    else:
        ref.staticType = resourceType
    return ref

def typeCheck(expr):
    expr = typecheck.typeCheck(expr)
    expr = typecheck.addDynTypeChecks(expr)
    return expr


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

        varBindings.append(makeFieldRef(relName, incarnation,
                                        columnId))

    def getCondition(self):
        subconds = []

        for binding in self.values():
            if len(binding) >= 2:
                subconds.append(nodes.Equal(*binding))

        if len(subconds) == 0:
            return None
        elif len(subconds) == 1:
            return typeCheck(subconds[0])
        else:
            return typeCheck(nodes.And(*subconds))

    def expandVariable(self, var):
        try:
            # Select an arbitrary binding.
            return iter(self[var.name]).next()
        except KeyError:
            return var

    def prettyPrint(self, stream=None, indent=0):
        if stream == None:
            stream = sys.stdout

        stream.write('Bindings:\n')
        pprint.pprint(self, stream, indent + 2)


class BasicMapper(rewrite.ExpressionTransformer):

    __slots__ = ('currentIncarnation')

    def __init__(self, prePrefix=None, postPrefix=""):
        super(BasicMapper, self).__init__(prePrefix=prePrefix,
                                          postPrefix=postPrefix)

        self.currentIncarnation = 0

    def makeIncarnation(self):
        self.currentIncarnation += 1
        return self.currentIncarnation


class AbstractSqlMapper(BasicMapper):

    __slots__ = ('scopeStack')

    RDF_TYPE = nodes.Uri(rdf.type)
    RDF_STATEMENT = nodes.Uri(rdf.Statement)
    RDF_SUBJECT = nodes.Uri(rdf.subject)
    RDF_PREDICATE = nodes.Uri(rdf.predicate)
    RDF_OBJECT = nodes.Uri(rdf.object)


    def __init__(self):
        super(AbstractSqlMapper, self).__init__(prePrefix='pre')

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

    def StatementPattern(self, expr, subject, pred, object):
        incarnation = self.makeIncarnation()

        conds = []
        for id, node in (('subject', subject), ('predicate', pred),
                         ('object', object)):
            if isinstance(node, nodes.Var):
                self.currentScope().addBinding(node.name, 'S',
                                               incarnation, id)
            else:
                ref = makeFieldRef('S', incarnation, id)
                conds.append(nodes.Equal(ref, node))

        rel = nodes.Relation('S', incarnation)
        if conds == []:
            return rel
        else:
            return nodes.Select(rel, nodes.And(*conds))

    def ReifStmtPattern(self, expr, var, subject, pred, object):
        return nodes.Product(self.StatementPattern(expr, var, self.RDF_TYPE,
                                                   self.RDF_STATEMENT),
                             self.StatementPattern(expr, var,
                                                   self.RDF_SUBJECT, subject),
                             self.StatementPattern(expr, var,
                                                   self.RDF_PREDICATE, pred),
                             self.StatementPattern(expr, var,
                                                   self.RDF_OBJECT, object))

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

    def MapResult(self, expr, *transfSubexprs):
        # Add an unique incarnation identifier.
        expr.incarnation = self.makeIncarnation()

        # FIXME: Add this mapping's columns to the current scope.
        return expr

    def Var(self, expr):
        return self.currentScope().expandVariable(expr)


class VersionMapper(rewrite.ExpressionTransformer):
    
    __slots__ = ('versionNumber')

    def __init__(self, versionNumber):
        super(VersionMapper, self).__init__(prePrefix='pre')

        self.versionNumber = versionNumber

    def Relation(self, expr):
        if expr.name != 'S':
            return expr

        incr = expr.incarnation

        rel = nodes.Product(nodes.Relation('version_statement', incr),
                            nodes.Relation('statements', incr))

        cond = nodes.And(
            nodes.Equal(
                nodes.FieldRef('version_statement', incr, 'version_id'),
                nodes.Literal(self.versionNumber)),
            nodes.Equal(
                nodes.FieldRef('version_statement', incr, 'stmt_id'),
                nodes.FieldRef('statements', incr, 'id')))

        return nodes.Select(rel, cond)

    def FieldRef(self, expr):
        if expr.relName != 'S':
            return expr

        return nodes.FieldRef('statements', expr.incarnation, expr.fieldId)

    def _dynTypeExpr(self, expr):
        typeExpr = expr.staticType

        if isinstance(typeExpr, LiteralType):
#             if typeExpr.typeUri is not None:
#                 # Search for the actual type id.
#                 incarnation = self.makeIncarnation()
#                 cond = nodes.Equal(nodes.FieldRef('data_types',
#                                                   incarnation, 'uri'),
#                                    nodes.Uri(typeExpr.typeUri))
#                 select = nodes.Select(nodes.Relation('data_types',
#                                                      incarnation),
#                                       cond)
#                 return nodes.MapResult(['id'],
#                                      nodes.FieldRef('data_types',
#                                                     incarnation, 'id'))
#             else:
#                 return TYPE_ID_LITERAL
            return nodes.Literal(TYPE_ID_LITERAL)
        elif isinstance(typeExpr, BlankNodeType):
            return nodes.Literal(TYPE_ID_BLANKNODE)
        elif isinstance(typeExpr, ResourceType):
            return nodes.Literal(TYPE_ID_RESOURCE)
        elif isinstance(typeExpr, RdfNodeType) and \
             isinstance(expr, nodes.FieldRef) and \
             expr.relName == 'S' and expr.fieldId == 'object':
            return nodes.FieldRef('statements', expr.incarnation,
                                  'object_type')
        else:
            assert False, "Cannot determine type"

    def preDynType(self, expr):
        return self._dynTypeExpr(expr[0]),

    def DynType(self, expr, subexpr):
        return subexpr

    def MapResult(self, expr, relExpr, *mappingExprs):
        expr[0] = relExpr
        for i, mappingExpr in enumerate(mappingExprs):
            expr.columnNames[i*2+1:i*2+1] = 'type__' + expr.columnNames[i*2],
            expr[i*2+2:i*2+2] = self._dynTypeExpr(expr[i*2+1]),
            expr[i*2+1] = mappingExpr
        return expr

    def _setOperation(self, expr, *operands):
        expr.columnNames = list(operands[0].columnNames)
        expr[:] = operands
        return expr

    Union = _setOperation
    SetDifference = _setOperation
    Intersection = _setOperation


class MultiVersionMapper(object):
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
