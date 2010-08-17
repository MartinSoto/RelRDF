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

import math
import time

import gtk
import goocanvas

import yapgvb as gv

import shapes
import units

from props import HierarchicalAttrBase, typedProp, delegateProp


engines = gv.engines


class Node(HierarchicalAttrBase):
    _defaults = {
        'label': '',
        }

    pos = delegateProp('_node', 'pos')
    width = delegateProp('_node', 'width')
    height = delegateProp('_node', 'height')

    def __init__(self, graph, name):
        self._parent = graph
        self._node = graph._graph.add_node(name)

        # Use name as default label.
        self.label = name

        # Clear the actual internal label.
        self._node.label = ''

    def _createItems(self, parentItem, view):
        self._node.shape = self.shape
        self._shape = shapes.getShapeFactory(self.shape)(self)
        w, h = self._shape.createItems(parentItem, view)
        self._node.width = w * units.TO_INCHES
        self._node.height = h * units.TO_INCHES

    def _placeItems(self, parentItem, view):
        x, y = self._node.pos
        self._shape.placeItems(parentItem, view,
                               x / units.TO_POINTS, y / units.TO_POINTS)


class Edge(HierarchicalAttrBase):
    _defaults = {
        'label': '',
        }

    arrowsize = delegateProp('_edge', 'arrowsize')
    label = delegateProp('_edge', 'label')
    lp = delegateProp('_edge', 'lp')
    pos = delegateProp('_edge', 'pos')

    def __init__(self, graph, start, end):
        self._parent = graph
        self._edge = graph._graph.add_edge(start._node, end._node)

    def _makeArrowHead(self, (x0, y0), (x1, y1), **attrs):
        x0, y0, x1, y1 = [l * units.TO_POINTS for l in x0, y0, x1, y1]
        scaleFactor = math.hypot(y1-y0, x0-x1)
        angle = -math.degrees(math.atan2(y1-y0, x0-x1))

        shape = goocanvas.Path(line_width=0,
                               fill_color=self.color,
                               data='M 0 0 L 1 0.25 L 1 -0.25 Z')
        shape.translate(x1, y1)
        shape.scale(scaleFactor, scaleFactor)
        shape.rotate(angle, 0, 0)

        return shape

    def _placeItems(self, parentItem, view):
        # Edge line:

        lineWidth = 2.0

        pos = self._edge.pos
        points = [(x / units.TO_POINTS, y / units.TO_POINTS) for
                  x, y in pos.points]

        data = 'M %f %f' % points[0]
        i = 1
        while i < len(points):
            (cx1, cy1), (cx2, cy2), (x, y) = points[i:i+3]
            data += ' C %s %s %s %s %s %s' % (cx1, cy1, cx2, cy2, x, y)
            i += 3

        shape = goocanvas.Path(line_width=lineWidth,
                               data=data,
                               stroke_color=self.color)
        parentItem.add_child(shape)

        # Label
        if self._edge.lp is not None:
            x, y = self._edge.lp
            labelLineBreakWidth = int(self.labelLineBreakWidth)
            alignment = self.labelAlignment
            text = goocanvas.Text(text=self.label,
                                  x=0,
                                  y=0,
                                  anchor=gtk.ANCHOR_CENTER,
                                  font=self.labelFont,
                                  alignment=alignment,
                                  use_markup=bool(self.labelUseMarkup),
                                  width=labelLineBreakWidth,
                                  fill_color = "black")
            text.scale(1.0, -1.0)
            text.translate(x / units.TO_POINTS, -y / units.TO_POINTS)
            parentItem.add_child(text)

        # Start arrow:
        if pos.start is not None:
            x, y = pos.start
            shape = self._makeArrowHead(points[0],
                                        (x / units.TO_POINTS,
                                         y / units.TO_POINTS))
            parentItem.add_child(shape)
            
        # End arrow:
        if pos.end is not None:
            x, y = pos.end
            shape = self._makeArrowHead(points[-1],
                                        (x / units.TO_POINTS,
                                         y / units.TO_POINTS))
            parentItem.add_child(shape)



class GraphBase(HierarchicalAttrBase):
    _defaults = {
        'shape': 'ellipse',
        'label': '',
        # This should be Sans, but this particular font works around a
        # layout bug in Pango.
        'labelFont': 'Bitstream Charter, 14',
        'labelAlignment': 'center',
        'labelUseMarkup': 'False',
        'labelLineBreakWidth': '0',

        'fillColor': 'white',
        'color': 'black',
        }

    bb = delegateProp('_graph', 'bb')
    mode = delegateProp('_graph', 'mode')
    # FIXME: Arrange for setting value in points instead of inches.
    nodesep = delegateProp('_graph', 'nodesep')
    overlap = delegateProp('_graph', 'overlap')
    pack = delegateProp('_graph', 'pack')
    packmode = delegateProp('_graph', 'packmode')
    rankdir = delegateProp('_graph', 'rankdir')
    # FIXME: Arrange for setting value in points instead of inches.
    ranksep = delegateProp('_graph', 'ranksep')

    def __init__(self, _graph, _parent=None):
        self._graph = _graph
        self._parent = _parent
        self._nodes = {}
        self._edges = set()
        self._subgraphs = {}

        # FIXME: yapgvb has problems with subgraph attributes.
        self.label = ''

        # Work around a bug in yapgvb, which fails to initialize the
        # auto_attach field in the CGraph class. If it happens to get
        # a false value, position attributes won't be set in the
        # graph. Calling this method we make sure that the value is
        # set to true.
        _graph.__set_auto_attach__(True)

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

    def _createItems(self, engine, parentItem, view):
        view.set_bounds(0, 0, 1000, 1000)

        # Set the label.
        if hasattr(self, 'label'):
            self._graph.label = self.label

        for node in self._nodes.values():
            node._createItems(parentItem, view)

        for graph in self._subgraphs.values():
            graph._createItems(engine, parentItem, view)

    def layout(self, engine, parentItem, view):
        # In GraphViz coordinate system, y grows downwards.
        parentItem.scale(1.0, -1.0)

        self._createItems(engine, parentItem, view)
        self._graph.layout(engine)
        self._placeItems(parentItem, view)

    def _placeItems(self, parentItem, view):
        x1, y1, x2, y2 = [l / units.TO_POINTS for l in self.bb]
        if self._parent is None:
            view.set_bounds(x1 - 30, -(y2 + 30), x2 + 30, -(y1 - 30))
        else:
            pass
#             # Paint the border around the cluster.
#             pntr.polygon(((x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)),
#                          style=self.clusterStyle

#             # Paint the label.
#             if self._graph.lp is not None:
#                 x, y = self._graph.lp
#                 x = x / units.TO_POINTS
#                 y = y / units.TO_POINTS

#                 font = pntr.getFont(self.clusterLabelFont
#                 w, h, d = font.getExtents(self.label)
#                 pntr.text((x, y - d), self.label,
#                           style=font.getCssProps() +
#                           self.clusterLabelStyle

        for node in self._nodes.values():
            node._placeItems(parentItem, view)

        for graph in self._subgraphs.values():
            graph.placeItems(parentItem, view)

        for edge in self._edges:
            edge._placeItems(parentItem, view)


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
