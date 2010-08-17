# -*- coding: utf-8 -*-
# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2010 Fraunhofer-Institut fuer Experimentelles
#                         Software Engineering (IESE).
#
# RelRDF is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.


import sys
import re


_protectPtrn = re.compile(r'[<&"]')

_protectSubstTable = {
    '<': '&lt;',
    '&': '&amp;',
    '"': '&quot;',
    }

def _substProtectedChar(match):
    return _protectSubstTable[match.group(0)]

def _protectText(text):
    return _protectPtrn.sub(_substProtectedChar, text).encode('utf8')


class Node(object):
    def __init__(self, id):
        self._id = id
        self._edges = {}

    def __str__(self):
        return "<Node '%s'>" % self._id


class Edge(object):
    def __init__(self, node1, node2):
        self._node1 = node1
        self._node2 = node2

    def __str__(self):
        return "<Edge '%s' -> '%s'>" % (self._node1, self._node2)


class XMLVisMaker(object):
    __slots__ = ('nodes',
                 'subgraphs')

    _pattern = re.compile(r'^(?:(edge_)|(cluster_))?([a-zA-Z_]+)([1-9][0-9]?)?$')

    def __init__(self):
        self.nodes = {}
        self.subgraphs = {}

    def getNode(self, name, cluster=None):
        name = unicode(name)
        try:
            node = self.nodes[name]
        except KeyError:
            if cluster is None:
                node = Node(name)
            else:
                node = Node(name)
            self.nodes[name] = node

        return node

    def getEdge(self, node1, node2):
        try:
            edge = node1._edges[node2]
        except KeyError:
            edge = Edge(node1, node2)
            node1._edges[node2] = edge

        return edge

    def getSubgraph(self, name):
        name = unicode(name)
        try:
            subgraph = self.subgraphs[name]
        except KeyError:
            subgraph = name
            self.subgraphs[name] = subgraph

        return subgraph

    @staticmethod
    def _getPropColList(propColDict, nodeNumber):
        try:
            return propColDict[nodeNumber]
        except KeyError:
            propColList = []
            propColDict[nodeNumber] = propColList
            return propColList

    def addResults(self, results):
        # Create data structures containing the indexes of the
        # relevant columns. Node numbers can go up to 99.

        # nodeIdCols[i] contains the column index of the column
        # specifying node<i+1>'s identifier.
        nodeIdCols = {}
        
        # nodePropCols[i] contains the column indexes of the columns
        # specifying node<i+1>'s property values. The value is a list
        # of pairs of the form (columnIndex, propName).
        nodePropCols = {}

        # Similar to nodePropCols but for the edges. edgePropCols[i]
        # contains the column indexes of the columns specifying
        # the properties of the edge between node<i+1> and node<i+2>.
        edgePropCols = {}

        # Similar to nodeIdCols and nodePropCols, but for clusters.
        clusterIdCols = {}
        clusterPropCols = {}

        # Fill the previous data structures using the column names.
        for i, colName in enumerate(results.columnNames):
            m = self._pattern.match(colName)
            if m is not None:
                (isEdge, isCluster, propName, nodeNumberStr) = m.groups()

                if nodeNumberStr is None:
                    if isEdge:
                        # For edges, node number defaults to 1. This
                        # is useful for the very common case of
                        # specifying only two nodes.
                        nodeNumber = 0
                    else:
                        # Ignore this column.
                        continue
                else:
                    nodeNumber = int(nodeNumberStr) - 1

                if isEdge:
                    if nodeNumber == 99:
                        # Doesn't make sense since the end node
                        # couldn't be specified (would be 100).
                        continue
                    self._getPropColList(edgePropCols, nodeNumber). \
                        append((i, propName))
                elif isCluster:
                    self._getPropColList(clusterPropCols, nodeNumber). \
                        append((i, propName))
                else:
                    if propName == 'node':
                        nodeIdCols[nodeNumber] = i
                    elif propName == 'cluster':
                        clusterIdCols[nodeNumber] = i
                    else:
                        self._getPropColList(nodePropCols, nodeNumber). \
                            append((i, propName))

        if len(nodeIdCols) == 0 and len(clusterIdCols) == 0:
            # No work to do.
            return

        # Iterate over the results creating nodes, edges and clusters.
        for result in results:
            # Maps node numbers to cluster objects.
            clusters = {}

            # Maps node numbers to node objects.
            nodes = {}

            # Process cluster definitions first, so that the
            # corresponding node can be put into the cluster.
            for nodeNumber, clusterIdCol in clusterIdCols.items():
                cluster = self.getSubgraph('cluster_' + result[clusterIdCol])

                # Set the cluster properties.
                for propColumn, propName in \
                        self._getPropColList(clusterPropCols, nodeNumber):
                    setattr(cluster, propName, result[propColumn])

                clusters[nodeNumber] = cluster

            for nodeNumber, nodeIdCol in nodeIdCols.items():
                try:
                    parent = clusters[nodeNumber]
                except KeyError:
                    parent = None
                node = self.getNode(result[nodeIdCol], None)

                # Set the node properties.
                for propColumn, propName in \
                        self._getPropColList(nodePropCols, nodeNumber):
                    setattr(node, propName, result[propColumn])

                nodes[nodeNumber] = node

            # There is an edge between all pairs of consecutive node
            # numbers.
            for nodeNumber, nodeIdCol in nodeIdCols.items():
                if (nodeNumber + 1) not in nodeIdCols:
                    continue

                edge = self.getEdge(nodes[nodeNumber], nodes[nodeNumber + 1])

                if nodeNumber in edgePropCols:
                    # Set the edge properties.
                    for propColumn, propName in edgePropCols[nodeNumber]:
                        setattr(edge, propName, result[propColumn])

    def serialize(self, startNodeName, outStr=sys.stdout, indent=0):
        startNode = self.nodes[startNodeName]

        serialized = set()

        outStr.write('  ' * indent + '<graph>\n')
        self._serializeNode(startNode, serialized, outStr, indent + 1)
        outStr.write('  ' * indent + '</graph>\n')

    def _serializeNode(self, node, serialized, outStr, indent):
        if node in serialized:
            outStr.write('  ' * indent +
                         '<ref id="%s" \>\n' % _protectText(node._id))
            return
        serialized.add(node)

        outStr.write('  ' * indent +
                     '<node id="%s">\n' % _protectText(node._id))

        for name, value in node.__dict__.iteritems():
            if name.startswith('_') or value is None:
                continue

            outStr.write('  ' * indent +
                         '<%s>%s</%s>\n' % (name, _protectText(value), name))

        for edge in node._edges.itervalues():
            self._serializeNode(edge._node2, serialized, outStr, indent + 1)

        outStr.write('  ' * indent + '</node>\n')


if __name__ == '__main__':
    import relrdf
    from relrdf.localization import _
    from relrdf.error import InstantiationError
    from relrdf.factory import parseCmdLineArgs


    def error(msg):
        print >> sys.stderr, _("error: %s") % msg
        sys.exit(1)


    if len(sys.argv) < 3:
        print >> sys.stderr, \
              _("usage: maker.py "
                ":<model base type> [<model base params] :<model type> "
                "[<model params>]")
        sys.exit(1)

    argv = list(sys.argv[1:])

    try:
        baseType, baseArgs = parseCmdLineArgs(argv, 'model base')
        modelBase = relrdf.getModelBase(baseType, **baseArgs)

        modelType, modelArgs = parseCmdLineArgs(argv, 'model')
        model = modelBase.getModel(modelType, **modelArgs)
    except InstantiationError, e:
        error(e)

    maker = XMLVisMaker()

    query = u"""
select ?node1 ?node2
where {
  ?node1 vmxt:enthält ?node2 .
}
"""
    results = model.query('SPARQL', query)
    maker.addResults(results)

    query = u"""
select ?node1 ?type1 ?name1 ?descr1
where {
  ?node1 rdf:type ?type1 .
  optional {
    ?node1 ?nameProp1 ?name1 .
    filter (?nameProp1 = vmxt:Name || ?nameProp1 = vmxt:Titel)
  }
  optional {
    ?node1 vmxt:Beschreibung ?descr1 .
  }
}
"""
    results = model.query('SPARQL', query)
    maker.addResults(results)

    sys.stdout.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
    maker.serialize('http://www.v-modell-xt.de/model/1#root')

    model.close()
    modelBase.close()
