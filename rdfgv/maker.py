import re


class RdfGraphvizMaker(object):
    __slots__ = ('graph',)

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

    _pattern = re.compile(r'^(edge_)?([a-zA-Z_]+)(1|2)?$')

    def __init__(self, graph):
        self.graph = graph

    def addResults(self, results):
        # Create data structures containing the indexes of the
        # relevant columns:

        pos = [None, None]
        props = [[], []]
        edgeProps = []

        for i, colName in enumerate(results.columnNames):
            m = self._pattern.match(colName)
            if m is not None:
                (edge, propName, nodeNumber) = m.groups()

                if edge is not None:
                    if nodeNumber is not None:
                        continue
                    if propName not in self._edgeProps:
                        continue
                    edgeProps.append((i, propName))
                elif nodeNumber is not None:
                    if propName == 'node':
                        pos[int(nodeNumber)-1] = i
                    else:
                        if propName not in self._nodeProps:
                            continue
                        props[int(nodeNumber)-1].append((i, propName))

        if pos[0] is None and pos[1] is None:
            return

        # Iterate over the results creating nodes and edges.

        for result in results:
            node = [None, None]

            for i in range(2):
                if pos[i] != None:
                    nodeId = result[pos[i]]
                    node[i] = self.graph.add_node(str(nodeId))

                    for (propPos, propName) in props[i]:
                        setattr(node[i], propName, result[propPos])

            if node[0] is not None and node[1] is not None:
                edge = self.graph.add_edge(node[0], node[1])
                
                for (propPos, propName) in edgeProps:
                   setattr(edge, propName, result[propPos])

