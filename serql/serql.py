import sys
import pprint

import antlr

import error
from tree import expression as expr
from tree import rewrite
import query


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

        varBindings.add(expr.FieldRef(relName, incarnation, columnId))

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
                subconds.append(expr.Equal(*binding))

        for group in self.independent:
            refs = []
            for var in group:
                refs.append(iter(self.bindings[var.name]).next())
            if len(group) >= 2:
                subconds.append(expr.Different(*refs))

        if len(subconds) == 0:
            return None
        elif len(subconds) == 1:
            return subconds[0]
        else:
            return expr.And(*subconds)

    def expandVariables(self, expr):
        def operation(expr, subexprsModif, *subexprs):
            assert isinstance(expr, query.Var)
            assert subexprsModif == False

            # Select an arbitrary binding.
            return iter(self.bindings[expr.name]).next(), True

        return rewrite.treeMatchApply(query.Var, operation, expr)[0]

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

    def __init__(self, *args, **kwargs):
        super(Parser, self).__init__(*args, **kwargs)

        try:
            self.query = kwargs['query']
        except KeyError:
            self.query = query.Query()

        # Set the standard SerQL predefined prefixes.
        self.query.setPrefix('rdf',
                             'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.query.setPrefix('rdfs',
                             'http://www.w3.org/2000/01/rdf-schema#')
        self.query.setPrefix('xsd',
                             'http://www.w3.org/2001/XMLSchema#')
        self.query.setPrefix('owl',
                             'http://www.w3.org/2002/07/owl#')
        self.query.setPrefix('serql',
                             'http://www.openrdf.org/schema/serql#')

    @staticmethod
    def exprFromTriple(context, subject, pred, object):
        incarnation = context.getIncarnation('S')

        conds = []
        for i, node in enumerate((subject, pred, object)):
            if isinstance(node, query.Var):
                context.addBinding(node.name, 'S', incarnation, i)
            else:
                ref = expr.FieldRef('S', incarnation, i)
                conds.append(expr.Equal(ref, node))

        rel = expr.Relation('S', incarnation)
        if conds == []:
            return rel
        else:
            return expr.Select(rel, expr.And(*conds))

    @staticmethod
    def exprFromPattern(context, nodeList1, edge, nodeList2):
        rels = []

        indepVar1 = None
        indepVar2 = None

        for node1 in nodeList1:
            for node2 in nodeList2:
                rels.append(Parser.exprFromTriple(context, node1,
                                                  edge, node2))

                if isinstance(node1, query.Var):
                    if indepVar1:
                        context.addIndependentPair(indepVar1, node1)
                    else:
                        indepVar1 = node1

                if isinstance(node2, query.Var):
                    if indepVar2:
                        context.addIndependentPair(indepVar2, node2)
                    else:
                        indepVar2 = node2

        if len(rels) > 1:
            return expr.Product(*rels)
        else:
            return rels[0]

    @staticmethod
    def graphPatternExpr(context, node):
        cond = context.getCondition()
        if cond:
            node = expr.Select(node, cond)
        return node

    @staticmethod
    def selectQueryExpr(context, (columnNames, mappingExprs), baseExpr):
        mapping = expr.Map('Answer', baseExpr,
                           *[context.expandVariables(mappingExpr)
                             for mappingExpr in mappingExprs])
        return expr.NameColumns(columnNames, mapping)
