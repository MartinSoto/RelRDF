import sys
import pprint

import antlr

import error
from expression import nodes
from expression import rewrite


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

    def addIndependentPair(self, var1, var2):
        if var1.name == var2.name:
            return

        group1 = self.indepMapping.get(var1.name)
        group2 = self.indepMapping.get(var2.name)

        if not group1 and not group2:
            group = frozenset((var1, var2))
        elif group1 and not group2:
            group = group1
        elif not group1 and group2:
            group = group2
        else:
            # Merge both groups.
            group = group1.union(group2)
            for var in group:
                self.indepMapping[var.name] = group

        self.indepMapping[var1.name] = group
        self.indepMapping[var2.name] = group

    def addReifPattern(self, subject, predicate, object):
        # Use a variable name that isn't allowed in SerQL.
        var = nodes.Var('#stmt_%d#' % self.reifPatternVarNr)
        self.reifPatternVarNr += 1

        self.reifPatterns.append(nodes.ReifStmtPattern(var, subject,
                                                       predicate, object))
        return var

    def getReifPatterns(self):
        return tuple(self.reifPatterns)

    def getCondition(self):
        subconds = []

        for group in self.independent:
            if len(group) >= 2:
                subconds.append(nodes.Different(*group))

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
                    line=expr.line, column=expr.column,
                    fileName=expr.fileName)

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

    # The standard SerQL predefined prefixes.
    basePrefixes = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'xsd': 'http://www.w3.org/2001/XMLSchema#',
        'owl': 'http://www.w3.org/2002/07/owl#',
        'serql': 'http://www.openrdf.org/schema/serql#'}


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

    def createLocalPrefix(self, prefix, uri):
        """Create a new local prefix `prefix` with associated URI
        `uri`."""
        self.localPrefixes[prefix] = uri

    def getPrefixUri(self, prefix):
        """Return the URI associated to namespace prefix `prefix`.

        Prefixes will be searched for first in the locally defined
        set, then in the external set provided when constructing the
        parser object, and finally in the predefined SerQL base set.

        A `KeyError` will be raised if the given prefix is not found."""
        try:
            return self.localPrefixes[prefix]
        except KeyError:
            try:
                return self.externalPrefixes[prefix]
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
                rels.append(nodes.StatementPattern(node1, edge, node2))

                if isinstance(node1, nodes.Var):
                    self.currentContext().addBound(node1.name)
                    if indepVar1:
                        self.currentContext() \
                            .addIndependentPair(indepVar1, node1)
                    else:
                        indepVar1 = node1

                if isinstance(edge, nodes.Var):
                    self.currentContext().addBound(edge.name)

                if isinstance(node2, nodes.Var):
                    self.currentContext().addBound(node2.name)
                    if indepVar2:
                        self.currentContext() \
                            .addIndependentPair(indepVar2, node2)
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
                    if indepVar1:
                        self.currentContext() \
                            .addIndependentPair(indepVar1, node1)
                    else:
                        indepVar1 = node1

                if isinstance(edge, nodes.Var):
                    self.currentContext().addBound(edge.name)

                if isinstance(node2, nodes.Var):
                    self.currentContext().addBound(node2.name)
                    if indepVar2:
                        self.currentContext() \
                            .addIndependentPair(indepVar2, node2)
                    else:
                        indepVar2 = node2

        return vars

    def graphPatternExpr(self, node):
        cond = self.currentContext().getCondition()
        if cond:
            node = nodes.Select(node, cond)
        return node

    def selectQueryExpr(self, (columnNames, mappingExprs), patternExpr,
                        condExpr):
        current = patternExpr

        patterns = self.currentContext().getReifPatterns()
        if len(patterns) > 0:
            # Add the reified statement patterns to the pattern
            # expression.
            current = nodes.Product(current, *patterns)

        if condExpr:
            self.currentContext().checkVariables(condExpr)
            current = nodes.Select(current, condExpr)

        for mappingExpr in mappingExprs:
            self.currentContext().checkVariables(mappingExpr)
        current = nodes.MapResult(columnNames, current, *mappingExprs)
        return current

    def resolveQName(self, qName):
        """Create a URI expression node corresponding to qualified
        name `qName`."""
        pos = qName.index(':')
        base = self.getPrefixUri(qName[:pos])
        return nodes.Uri(base + qName[pos + 1:])

    def expandQNames(self, expr):
        """Expand all QName nodes in `expr` into their corresponding
        URIs."""

        def postOp(expr, subexprsModif):
            assert isinstance(expr, nodes.QName)
            assert subexprsModif == False

            try:
                return self.resolveQName(expr.qname), True
            except KeyError:
                raise error.SemanticError(
                    msg=_("Undefined namespace prefix '%s'") % expr.qname,
                    line=expr.line, column=expr.column,
                    fileName=expr.fileName)

        return rewrite.exprMatchApply(expr, nodes.QName, postOp=postOp)[0]

    def checkPrefix(self, token):
        if token.getText() == '_':
            raise error.SyntaxError(msg=_("Invalid namespace prefix '_'"),
                                    line=token.getLine(),
                                    column=token.getColumn(),
                                    fileName=self.getFilename())
        return token.getText()
