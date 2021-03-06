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

import re


class RdfGraphvizMaker(object):
    __slots__ = ('graph',
                 'subgraphs')

    _subgraphProps = set([
        'color',
        'fillcolor',
        'fontcolor',
        'fontname',
        'label', 
        'labeljust',
 	'labelloc',
        'style'])

    _nodeProps = set([
        'color',
        'colorscheme',
        'comment',
        'distortion',
        'fillcolor',
        'fixedsize',
        'fontcolor',
        'fontname',
        'fontsize',
        'group',
        'height',
        'label',
        'layer',
        'margin',
        'nojustify',
        'orientation',
        'peripheries',
        'pin',
        'pos',
        'rects',
        'regular',
        'root',
        'shape',
        'shapefile',
        'showboxes',
        'sides',
        'skew',
        'style',
        'target',
        'tooltip',
        'URL',
        'vertices',
        'width',
        'z'])

    _edgeProps = set([
        'arrowhead', 
        'arrowsize', 
        'arrowtail', 
        'color', 
        'colorscheme', 
        'comment', 
        'constraint', 
        'decorate', 
        'dir', 
        'fontcolor', 
        'fontname', 
        'fontsize', 
        'graph', 
        'head', 
        'headclip', 
        'headhref', 
        'headlabel', 
        'headport', 
        'headtarget', 
        'headtooltip', 
        'headURL', 
        'href', 
        'label', 
        'labelangle', 
        'labeldistance', 
        'labelfloat', 
        'labelfontcolor', 
        'labelfontname', 
        'labelfontsize', 
        'layer', 
        'len', 
        'lhead', 
        'lp', 
        'ltail', 
        'minlen', 
        'nojustify', 
        'pos', 
        'samehead', 
        'sametail', 
        'showboxes', 
        'style', 
        'tail', 
        'tailclip', 
        'tailhref', 
        'taillabel', 
        'tailport', 
        'tailtarget', 
        'tailtooltip', 
        'tailURL', 
        'target', 
        'tooltip', 
        'URL', 
        'weight'
        ])

    _pattern = re.compile(r'^(?:(edge_)|(cluster_))?([a-zA-Z_]+)(1|2)?$')

    def __init__(self, graph):
        self.graph = graph
        self.subgraphs = {}

        # FIXME: Yapgvb seems not to accept subgraph attributes if
        # they weren't set for the main graph first.
        self.graph.label = ''
        self.graph.style = 'filled'
        self.graph.fillcolor = 'white'

    def getSubgraph(self, name):
        name = unicode(name).encode('utf-8')
        try:
            subgraph = self.subgraphs[name]
        except KeyError:
            subgraph = self.graph.subgraph(name)
            self.subgraphs[name] = subgraph

        return subgraph

    def addResults(self, results):
        # Create data structures containing the indexes of the
        # relevant columns:

        pos = [None, None]
        props = [[], []]

        cluster_pos = [None, None]
        cluster_props = [[], []]

        edgeProps = []

        for i, colName in enumerate(results.columnNames):
            m = self._pattern.match(colName)
            if m is not None:
                (isEdge, isCluster, propName, nodeNumber) = m.groups()

                if isEdge:
                    if nodeNumber is not None:
                        continue
                    if propName not in self._edgeProps:
                        continue
                    edgeProps.append((i, propName))
                elif isCluster:
                    if nodeNumber is None:
                        continue
                    if propName not in self._subgraphProps:
                        continue
                    cluster_props[int(nodeNumber)-1].append((i, propName))
                elif nodeNumber is not None:
                    if propName == 'node':
                        pos[int(nodeNumber)-1] = i
                    elif propName == 'cluster':
                        cluster_pos[int(nodeNumber)-1] = i
                    else:
                        if propName not in self._nodeProps:
                            continue
                        props[int(nodeNumber)-1].append((i, propName))

        if pos[0] is None and pos[1] is None and \
           cluster_pos[0] is None and cluster_pos[1] is None:
            return

        # Iterate over the results creating nodes, edges and clusters.

        for result in results:
            cluster = [None, None]
            node = [None, None]

            for i in range(2):
                if cluster_pos[i] is not None:
                    clusterId = result[cluster_pos[i]]
                    cluster[i] = self.getSubgraph('cluster_' + clusterId)

                    for (propPos, propName) in cluster_props[i]:
                        setattr(cluster[i], propName,
                                unicode(result[propPos]).encode('utf-8'))

            for i in range(2):
                if pos[i] is not None:
                    nodeId = result[pos[i]]
                    if cluster[i] is None:
                        node[i] = self.graph.add_node(str(nodeId))
                    else:
                        node[i] = cluster[i].add_node(str(nodeId))

                    for (propPos, propName) in props[i]:
                        setattr(node[i], propName,
                                unicode(result[propPos]).encode('utf-8'))

            if node[0] is not None and node[1] is not None:
                edge = self.graph.add_edge(node[0], node[1])
                
                for (propPos, propName) in edgeProps:
                   setattr(edge, propName,
                           unicode(result[propPos]).encode('utf-8'))

