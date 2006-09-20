import yapgvb as gv

import shapes
import units
import painter


engines = gv.engines


def _nodeProp(name):
    def getProp(self):
        return getattr(self._node, name)

    return property(getProp)

class Node(object):
    def __init__(self, graph, name):
        self._graph = graph
        self._node = graph._graph.add_node(name)

        # Use name as default label.
        self.label = name

        # Clear the actual internal label.
        self._node.label = ''

    pos = _nodeProp('pos')
    width = _nodeProp('width')
    height = _nodeProp('height')

    _defaults = {
        'label': '',
        }

    def _getProp(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            try:
                return self._defaults[name]
            except KeyError:
                return self._graph._getProp(name)

    def _layout(self, pntr):
        shape = self._getProp('shape')
        self._node.shape = shape
        self._shape = shapes.getShapeFactory(shape)()
        w, h = self._shape.layout(self, pntr)
        self._node.width = w * units.TO_INCHES
        self._node.height = h * units.TO_INCHES

    def _paint(self, pntr):
        x, y = self._node.pos
        self._shape.paint(self, pntr,
                          x / units.TO_POINTS, y / units.TO_POINTS)


def _edgeProp(name):
    def getProp(self):
        return getattr(self._edge, name)

    return property(getProp)

class Edge(object):
    def __init__(self, graph, start, end):
        self._graph = graph
        self._edge = graph._graph.add_edge(start._node, end._node)

    pos = _edgeProp('pos')

    _defaults = {
        'label': '',
        }

    def _getProp(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            try:
                return self._defaults[name]
            except KeyError:
                return self._graph._getProp(name)

    def _paint(self, pntr):
        pos = self._edge.pos
        points = [(x / units.TO_POINTS, y / units.TO_POINTS) for
                  x, y in pos.points]

        pntr.openPath(style=self._getProp('edgeStyle'))
        pntr.moveTo(points[0])
        i = 1
        while i < len(points):
            pntr.curveTo(*points[i:i+3])
            i += 3
        pntr.closePath()

        if pos.start is not None:
            x, y = pos.start
            pntr.arrowHead(points[0],
                           (x / units.TO_POINTS, y / units.TO_POINTS),
                           style=self._getProp('arrowStyle'))
            
        if pos.end is not None:
            x, y = pos.end
            pntr.arrowHead(points[-1],
                           (x / units.TO_POINTS, y / units.TO_POINTS),
                           style=self._getProp('arrowStyle'))

def _graphProp(name):
    def getProp(self):
        return getattr(self._graph, name)

    def setProp(self, value):
        return setattr(self._graph, name, value)

    return property(getProp, setProp)

class GraphBase(object):
    def __init__(self, _graph, _parent=None):
        self._graph = _graph
        self._parent = _parent
        self._nodes = {}
        self._edges = set()
        self._subgraphs = {}

        # FIXME: yapgvb has problems with subgraph attributes.
        self.label = ''

    def subgraph(self, name):
        subgraph = GraphBase(self._graph.subgraph(name), self)
        self._subgraphs[name] = subgraph
        return subgraph

    def add_node(self, name, **attributes):
        try:
            node = self._nodes[name]
        except KeyError:
            node = Node(self, name)
            self._nodes[name] = node

        for attr, value in attributes.items():
            setattr(node, attr, value)
        return node

    def add_edge(self, start, end):
        edge = Edge(self, start, end)
        self._edges.add(edge)
        return edge

    def _layout(self, engine, pntr):
        # Set the label.
        if hasattr(self, 'label'):
            self._graph.label = self.label

        for node in self._nodes.values():
            node._layout(pntr)

        for graph in self._subgraphs.values():
            graph._layout(engine, pntr)

    def layout(self, engine, pntr):
        self._layout(engine, pntr)
        self._graph.layout(engine)

    def render(self, fileName):
        self._graph.render(fileName)

    def paint(self, pntr):
        x1, y1, x2, y2 = [l / units.TO_POINTS for l in self.bb]
        if self._parent is None:
            pntr.open(x2 - x1, y2 - y1)
        else:
            # Paint the border around the cluster.
            pntr.polygon(((x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)),
                         style=self._getProp('clusterStyle'))

            # Paint the label.
            if self._graph.lp is not None:
                x, y = self._graph.lp
                x = x / units.TO_POINTS
                y = y / units.TO_POINTS

                font = pntr.getFont(self._getProp('clusterLabelFont'))
                w, h, d = font.getExtents(self.label)
                pntr.text((x, y - d), self.label,
                          style=font.getCssProps() +
                          self._getProp('clusterLabelStyle'))

        for node in self._nodes.values():
            node._paint(pntr)

        for graph in self._subgraphs.values():
            graph.paint(pntr)

        for edge in self._edges:
            edge._paint(pntr)

        if self._parent is None:
            pntr.close()

    bb = _graphProp('bb')
    overlap = _graphProp('overlap')
    rankdir = _graphProp('rankdir')
    nodesep = _graphProp('nodesep')

    _defaults = {
        'arrowStyle': 'stroke: black; stroke-width:0; fill: black;',
        'clusterStyle': 'stroke: black; fill: white;',
        'clusterLabelFont': 'Sans, bold 14',
        'clusterLabelStyle': 'fill: black;',
        'edgeStyle': 'stroke: black; fill: none;',
        'label': '',
        'labelFont': 'Sans, 14',
        'labelMargin': 0.15,
        'labelStyle': '',
        'nodeStyle': 'stroke: black; fill: white;',
        'shape': 'ellipse',
        }

    def _getProp(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if self._parent is not None:
                return self._parent._getProp(name)
            else:
                return self._defaults.get(name)


class Graph(GraphBase):
    def __init__(self, _graph=None):
        if _graph is None:
            super(Graph, self).__init__(gv.Graph())
        else:
            super(Graph, self).__init__(_graph)


class Digraph(GraphBase):
    def __init__(self, _graph=None):
        if _graph is None:
            super(Digraph, self).__init__(gv.Digraph())
        else:
            super(Digraph, self).__init__(_graph)
