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

import gtk
import pango
import goocanvas

import units
from props import HierarchicalAttrBase, propPangoAlignment


class SimpleShape(HierarchicalAttrBase):
    __slots__ = ('_parent',
                 'group')

    labelAlignment = propPangoAlignment('labelAlignment')

    def __init__(self, node):
        self._parent = node

    def createItems(self, parentItem, view):
        self.group = goocanvas.Group()
        parentItem.add_child(self.group)

        # Create the label.
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
        self.group.add_child(text)

        # Determine the text bounds and use them to create the shape.
        textb = view.get_item_view(text).get_bounds()
        tw, th = textb.x2 - textb.x1, textb.y2 - textb.y1
        shape, w, h = self.makeShape(self.group, tw, th)

        if labelLineBreakWidth > 0:
            if alignment == pango.ALIGN_LEFT:
                text.props.x += labelLineBreakWidth / 2 - tw / 2
            elif alignment == pango.ALIGN_RIGHT:
                text.props.x -= labelLineBreakWidth / 2 - tw / 2

        # Set shape properties.
        shape.props.stroke_color = self.color
        shape.props.fill_color = self.fillColor

        # Put the text above the shape.
        text.raise_(None)

        return w, h

    def makeShape(self, parentItem, view, w, h):
        raise NotImplementedError

    def placeItems(self, parentItem, view, x, y):
        self.group.translate(x, y)


class Box(SimpleShape):
    __slots__ = ()

    def makeShape(self, parentItem, w, h):
        margin = 10.0
        borderWidth = 2.0

        w += 2 * margin
        h += 2 * margin
        shape = goocanvas.Rect(x=-w/2, y=-h/2, width=w, height=h,
                               line_width=borderWidth)
        parentItem.add_child(shape)

        return shape, w, h


class Parallelogram(SimpleShape):
    __slots__ = ()

    def makeShape(self, parentItem, w, h):
        margin = 10.0
        borderWidth = 2.0

        w /= 0.6
        h += 2 * margin
        shape = goocanvas.Path(line_width=borderWidth,
                               data="M %f %f L %f %f L %f %f L %f %f Z" %
                               (-w / 2, -h / 2,
                                -w * 0.3, h / 2,
                                w / 2, h / 2,
                                w * 0.3, -h / 2))
        parentItem.add_child(shape)

        return shape, w, h


class Ellipse(SimpleShape):
    __slots__ = ()

    C = 0.75
    WF = math.sqrt(1 + C**2)
    HF = math.sqrt(1 + 1/C**2)

    def makeShape(self, parentItem, w, h):
        margin = 10.0
        borderWidth = 2.0

        w = (w + margin) * self.WF
        h = (h + margin) * self.HF

        shape = goocanvas.Ellipse(line_width=borderWidth,
                                  center_x = 0,
                                  center_y = 0,
                                  radius_x = w / 2,
                                  radius_y = h / 2)
        parentItem.add_child(shape)

        return shape, w, h


_shapeClasses = {
    'box': Box,
    'ellipse': Ellipse,
    'parallelogram': Parallelogram
    }


def getShapeFactory(shapeName):
    try:
        return _shapeClasses[str(shapeName).lower()]
    except KeyError:
        assert False, "Shape '%s' not found" % shapeName
