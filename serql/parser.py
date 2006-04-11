import sys
import pprint

import antlr

import error
import commonns
from expression import nodes
from expression import rewrite
from expression import literal
from expression import uri


class SelectContext(object):
    """A container for contextual information associated to a single
    SerQL SELECT statement."""

    __slots__ = ('bound',
                 'indepMapping',
                 'reifPatternVarNr',
                 'reifPatterns')

    def __init__(self):
        self.bound = set()
        self.indepMapping = {}
        self.reifPatternVarNr = 1
        self.reifPatterns = []

    def getIndependent(self):
        return frozenset(self.indepMapping.values())

    independent = property(getIndependent)

    def addBound(self, varName):
        self.bound.add(varName)

    def addIndependentPair(self, varName1, varName2):
        if varName1 == varName2:
            return

        group1 = self.indepMapping.get(varName1)
        group2 = self.indepMapping.get(varName2)

        if not group1 and not group2:
            group = frozenset((varName1, varName2))
        elif group1 and not group2:
            group = group1
        elif not group1 and group2:
            group = group2
        else:
            # Merge both groups.
            group = group1.union(group2)
            for varName in group:
                self.indepMapping[varName] = group

        self.indepMapping[varName1] = group
        self.indepMapping[varName2] = group

    def addReifPattern(self, subject, predicate, object):
        # Use a variable name that isn't allowed in SerQL.
        var = nodes.Var('#stmt_%d#' % self.reifPatternVarNr)
        self.reifPatternVarNr += 1

        expr = nodes.ReifStmtPattern(var, subject,
                                     predicate, object)
        expr.setStartSubexpr(subject)
        var.setExtents(expr.getExtents())
        self.reifPatterns.append(expr)
        return var

    def getReifPatterns(self):
        return tuple(self.reifPatterns)

    def getCondition(self):
        subconds = []

        for group in self.independent:
            if len(group) >= 2:
                subconds.append(nodes.Different(*[nodes.Var(n)
                                                  for n in group]))

        if len(subconds) == 0:
            return None
        elif len(subconds) == 1:
            return subconds[0]
        else:
            return nodes.And(*subconds)

    def checkVariables(self, expr):
        def postOp(expr, subexprsModif):
            assert isinstance(expr, nodes.Var)
            assert subexprsModif == False

            if not expr.name in self.bound:
                raise error.SemanticError(
                    msg=_("Unbound variable '%s'") % expr.name,
                    extents=expr.getExtents())

            return expr, False

        return rewrite.exprMatchApply(expr, nodes.Var, postOp=postOp)[0]

    def prettyPrint(self, stream=None, indent=0):
        if stream == None:
            stream = sys.stdout

        stream.write('Bound:\n')
        pprint.pprint(self.bound, stream, indent + 2)
        stream.write('\nIndependent groups:\n')
        pprint.pprint(self.independent, stream, indent + 2)
        stream.write('\Reified statement patterns:\n')
        pprint.pprint(self.reifPatterns, stream, indent + 2)


class Parser(antlr.LLkParser):
    """The base class for the SerQL parser generated by ANTLR."""

    __slots__ = ('contextStack',

                 'externalPrefixes',
                 'localPrefixes')

    # The standard SerQL predefined prefixes, and the relrdf prefix.
    basePrefixes = {
        'rdf': commonns.rdf,
        'rdfs': commonns.rdfs,
        'xsd': commonns.xsd,
        'owl': commonns.owl,
        'serql': commonns.serql,
        'relrdf': commonns.relrdf}


    def __init__(self, *args, **kwargs):
        """Initializes a Parser object.

        If a keyword argument 'prefixes' is provided, it will be
        expected to be a dictionary containing predefined namespace
        prefix bindings intended to be used in addition to the
        standard SerQL prefixes. See `Parser.getPrefixUri` for
        details."""
        super(Parser, self).__init__(*args, **kwargs)

        # A stack of SelectContext objects, to handle nested SELECT
        # queries.
        self.contextStack = []

        try:
            self.externalPrefixes = kwargs['prefixes']
        except KeyError:
            self.externalPrefixes = {}

        # The set of locally defined namespace prefixes (prefixes
        # defined by the query itself through the USING NAMESPACE
        # clause.)
        self.localPrefixes = {}

    def pushContext(self):
        """Push a new select context into the context stack."""
        self.contextStack.append(SelectContext())

    def popContext(self):
        """Pop the topmost context form the context stack and return
        it."""
        return self.contextStack.pop()

    def currentContext(self):
        """Return the current (topmost) context."""
        return self.contextStack[-1]

    def createLocalPrefix(self, prefix, uriStr):
        """Create a new local prefix `prefix` with associated URI
        `uri`."""
        self.localPrefixes[prefix] = uri.Namespace(uriStr)

    def getPrefixUri(self, prefix):
        """Return the uri.Namespace object associated to namespace
        prefix `prefix`.

        Prefixes will be searched for first in the locally defined
        set, then in the external set provided when constructing the
        parser object, and finally in the predefined SerQL base set.

        A `KeyError` will be raised if the given prefix is not found."""
        try:
            return self.localPrefixes[prefix]
        except KeyError:
            try:
                return uri.Namespace(self.externalPrefixes[prefix])
            except KeyError:
                return self.basePrefixes[prefix]


    #
    # Expression Construction and Transformation
    #

    def exprFromPattern(self, nodeList1, edge, nodeList2):
        rels = []

        indepVar1 = None
        indepVar2 = None

        for node1 in nodeList1:
            for node2 in nodeList2:
                rels.append(nodes.StatementPattern(node1.copy(),
                                                   edge.copy(),
                                                   node2.copy()))

                if isinstance(node1, nodes.Var):
                    self.currentContext().addBound(node1.name)
                    if indepVar1 is not None:
                        self.currentContext() \
                            .addIndependentPair(indepVar1.name, node1.name)
                    else:
                        indepVar1 = node1

                if isinstance(edge, nodes.Var):
                    self.currentContext().addBound(edge.name)

                if isinstance(node2, nodes.Var):
                    self.currentContext().addBound(node2.name)
                    if indepVar2 is not None:
                        self.currentContext() \
                            .addIndependentPair(indepVar2.name, node2.name)
                    else:
                        indepVar2 = node2

        if len(rels) > 1:
            return nodes.Product(*rels)
        else:
            return rels[0]

    def exprListFromReifPattern(self, nodeList1, edge, nodeList2):
        vars = []

        indepVar1 = None
        indepVar2 = None

        for node1 in nodeList1:
            for node2 in nodeList2:
                vars.append(self.currentContext().addReifPattern(node1, edge,
                                                                 node2))

                if isinstance(node1, nodes.Var):
                    self.currentContext().addBound(node1.name)
                    if indepVar1 is not None:
                        self.currentContext() \
                            .addIndependentPair(indepVar1.name, node1.name)
                    else:
                        indepVar1 = node1

                if isinstance(edge, nodes.Var):
                    self.currentContext().addBound(edge.name)

                if isinstance(node2, nodes.Var):
                    self.currentContext().addBound(node2.name)
                    if indepVar2 is not None:
                        self.currentContext() \
                            .addIndependentPair(indepVar2.name, node2.name)
                    else:
                        indepVar2 = node2

        return vars

    def selectQueryExpr(self, (columnNames, mappingExprs), patternExpr,
                        condExpr):
        current = patternExpr

        patterns = self.currentContext().getReifPatterns()
        if len(patterns) > 0:
            # Add the reified statement patterns to the pattern
            # expression.
            current = nodes.Product(current, *patterns)

        indepCond = self.currentContext().getCondition()
        if indepCond is not None:
            current = nodes.Select(current, indepCond)

        if condExpr is not None:
            self.currentContext().checkVariables(condExpr)
            current = nodes.Select(current, condExpr)

        for mappingExpr in mappingExprs:
            self.currentContext().checkVariables(mappingExpr)
        current = nodes.MapResult(columnNames, current, *mappingExprs)
        return current

    def setOperationExpr(self, factory, expr1, expr2):
        expr = factory(expr1, expr2)

        if expr1.columnNames != expr2.columnNames:
            raise error.SemanticError(
                msg=_("Invalid set operation: result columns do not match"),
                extents=expr.getExtents())

        expr.columnNames = expr1.columnNames

        return expr

    def resolveQName(self, qName):
        """Create an URI expression node corresponding to qualified
        name `qName`."""
        pos = qName.index(':')
        namespace = self.getPrefixUri(qName[:pos])
        return nodes.Uri(namespace[qName[pos + 1:]])

    def expandQNames(self, expr):
        """Expand all QName nodes in `expr` into their corresponding
        URIs."""

        def postOp(expr, subexprsModif):
            assert isinstance(expr, nodes.QName)
            assert subexprsModif == False

            try:
                newExpr = self.resolveQName(expr.qname)
                newExpr.setExtents(expr.getExtents())
                return newExpr, True
            except KeyError:
                raise error.SemanticError(
                    msg=_("Undefined namespace prefix '%s'") % \
                    expr.qname[:expr.qname.index(':')],
                    extents=expr.getExtents())

        return rewrite.exprMatchApply(expr, nodes.QName, postOp=postOp)[0]

    def checkPrefix(self, token):
        if token.getText() == '_':
            extents = nodes.NodeExtents()
            extents.setFromToken(token, self)
            raise error.SyntaxError(msg=_("Invalid namespace prefix '_'"),
                                    extents=extents)
        return token.getText()


    #
    # Token Postprocessing
    #

    def convertLiteral(self, text):
        if text[0] == '@':
            return literal.Literal(text[3:], lang=text[1:3])
        elif text[0] == '<':
            endUri = text.find('>')
            return literal.Literal(text[endUri+1:],
                                   typeUri=uri.Uri(text[1:endUri]))
        else:
            assert False
