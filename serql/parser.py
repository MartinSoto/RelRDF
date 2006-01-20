import sys
import pprint

import antlr

import error
from expression import nodes
from expression import rewrite


class Var(nodes.ExpressionNode):
    """An expression node representing a SerQL variable by name."""

    __slots = ('name')

    def __init__(self, name):
        super(Var, self).__init__()

        self.name = name

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.name)


class SelectContext(object):
    """A container for contextual information associated to a single
    SerQL SELECT statement."""

    __slots__ = ('incarnations',
                 'bindings',
                 'indepMapping')

    def __init__(self):
        self.incarnations = {}
        self.bindings = {}
        self.indepMapping = {}

    def getIndependent(self):
        return frozenset(self.indepMapping.values())

    independent = property(getIndependent)

    def addBinding(self, varName, relName, incarnation, columnId):
        try:
            varBindings = self.bindings[varName]
        except KeyError:
            varBindings = set()
            self.bindings[varName] = varBindings

        varBindings.add(nodes.FieldRef(relName, incarnation, columnId))

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

    def getIncarnation(self, relName):
        incarnation = self.incarnations.get(relName, 0) + 1
        self.incarnations[relName] = incarnation
        return incarnation

    def getCondition(self):
        subconds = []

        for binding in self.bindings.values():
            if len(binding) >= 2:
                subconds.append(nodes.Equal(*binding))

        for group in self.independent:
            refs = []
            for var in group:
                refs.append(iter(self.bindings[var.name]).next())
            if len(group) >= 2:
                subconds.append(nodes.Different(*refs))

        if len(subconds) == 0:
            return None
        elif len(subconds) == 1:
            return subconds[0]
        else:
            return nodes.And(*subconds)

    def expandVariables(self, expr):
        def operation(expr, subexprsModif, *subexprs):
            assert isinstance(expr, Var)
            assert subexprsModif == False

            # Select an arbitrary binding.
            return iter(self.bindings[expr.name]).next(), True

        return rewrite.treeMatchApply(Var, operation, expr)[0]

    def prettyPrint(self, stream=None, indent=0):
        if stream == None:
            stream = sys.stdout

        stream.write('Incarnations:\n')
        pprint.pprint(self.incarnations, stream, indent + 2)
        stream.write('\nBindings:\n')
        pprint.pprint(self.bindings, stream, indent + 2)
        stream.write('\nIndependent groups:\n')
        pprint.pprint(self.independent, stream, indent + 2)


class Parser(antlr.LLkParser):
    """The base class for the SerQL parser generated by ANTLR."""

    __slots__ = ('prefixes')


    # The standard SerQL predefined prefixes.
    basePrefixes = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'xsd': 'http://www.w3.org/2001/XMLSchema#',
        'owl': 'http://www.w3.org/2002/07/owl#',
        'serql': 'http://www.openrdf.org/schema/serql#'}


    def __init__(self, *args, **kwargs):
        super(Parser, self).__init__(*args, **kwargs)

        try:
            self.prefixes = kwargs['prefixes']
        except KeyError:
            self.prefixes = {}

    def getPrefixUri(self, prefix):
        # FIXME: Produce appropriate exception.
        try:
            return self.prefixes[prefix]
        except KeyError:
            return self.basePrefixes[prefix]

    def resolveQName(self, qName):
        pos = qName.index(':')
        base = self.getPrefixUri(qName[:pos])
        return base + qName[pos + 1:]

    @staticmethod
    def exprFromTriple(context, subject, pred, object):
        incarnation = context.getIncarnation('S')

        conds = []
        for i, node in enumerate((subject, pred, object)):
            if isinstance(node, Var):
                context.addBinding(node.name, 'S', incarnation, i)
            else:
                ref = nodes.FieldRef('S', incarnation, i)
                conds.append(nodes.Equal(ref, node))

        rel = nodes.Relation('S', incarnation)
        if conds == []:
            return rel
        else:
            return nodes.Select(rel, nodes.And(*conds))

    @staticmethod
    def exprFromPattern(context, nodeList1, edge, nodeList2):
        rels = []

        indepVar1 = None
        indepVar2 = None

        for node1 in nodeList1:
            for node2 in nodeList2:
                rels.append(Parser.exprFromTriple(context, node1,
                                                  edge, node2))

                if isinstance(node1, Var):
                    if indepVar1:
                        context.addIndependentPair(indepVar1, node1)
                    else:
                        indepVar1 = node1

                if isinstance(node2, Var):
                    if indepVar2:
                        context.addIndependentPair(indepVar2, node2)
                    else:
                        indepVar2 = node2

        if len(rels) > 1:
            return nodes.Product(*rels)
        else:
            return rels[0]

    @staticmethod
    def graphPatternExpr(context, node):
        cond = context.getCondition()
        if cond:
            node = nodes.Select(node, cond)
        return node

    @staticmethod
    def selectQueryExpr(context, (columnNames, mappingExprs), baseExpr,
                        condExpr):
        current = baseExpr
        if condExpr:
            current = nodes.Select(current, context.expandVariables(condExpr))
        current = nodes.Map('Answer', current,
                            *[context.expandVariables(mappingExpr)
                              for mappingExpr in mappingExprs])
        current = nodes.NameColumns(columnNames, current)
        return current
