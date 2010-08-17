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

from __future__ import division

import gtk
import goocanvas

from kiwi.tasklet import WaitForSignal, get_event
from util import initTask, signalTask


class CanvasWidget(gtk.ScrolledWindow):
    """A GooCanvas based canvas widget with enhanced interaction.

    Currently the canvas supports interactive scrolling with various
    scroll modes (best fit, fit height, fit width, percent, see
    `setScale`) and selectable tools (see `setTool`).
    """

    __slots__ = ('cvView',
                 'cvModel',
                 'scaleMethod',
                 'scaleArgs')


    @initTask
    def __init__(self):
        super(CanvasWidget, self).__init__()

        self.set_shadow_type(gtk.SHADOW_IN)

        self.cvView = goocanvas.CanvasView()
        self.cvView.set_size_request(600, 450)
        self.cvView.show()
        self.add(self.cvView)
        
        self.cvModel = goocanvas.CanvasModelSimple()
        self.cvView.set_model(self.cvModel)

        # Scale is set by calling the setScale method with certain
        # arguments. These are stored as attributes, in order to be
        # able to reset the scale whenever it is necessary (e.g., when
        # the window size changes.)
        self.scaleMethod = None
        self.scaleArgs = ()
        self.connect('size-allocate', self.on__size_allocate)

        # Wait until the widget is realized.
        yield (WaitForSignal(self.cvView, 'realize'))
        tEvent = get_event()

        # Initialize tool support.
        self.cvView.connect('button-press-event',
                            self.on_canvas__button_press_event)
        self.setTool(self.TOOL_OPERATE)


    def getCanvas(self):
        return self.cvModel

    def getCanvasView(self):
        return self.cvView


    #
    # Scale Setting
    #

    def setScale(self, method, *args):
        """Set the canvas's scale.

        Scale will be set by calling `method` with the given
        arguments. Method must be one of the methods in this class
        having a name starting with 'scale'."""
        self.scaleMethod = method
        self.scaleArgs = args
        self._refreshScale()

    def _refreshScale(self):
        if self.scaleMethod is not None:
            self.scaleMethod(self, *self.scaleArgs)

    def scalePercent(self, percent):
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.cvView.set_scale(float(percent) / 100)

    # The "fit" scale methods cannot use the automatic policy, because
    # that easily leads to infinite loops (diagram is too tall -> add
    # scrollbar -> there is less space, so diagram is narrower and
    # less tall -> no scrollbar needed -> there is more space ->
    # diagram is wider and taller -> add scrollbar -> ...)

    def scaleBestFit(self):
        # Scrollbars aren't necessary, the diagram must always fit the
        # window.
        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)

        bounds = self.cvView.get_bounds()
        width, height = bounds.x2 - bounds.x1 + 1, bounds.y2 - bounds.y1 +1

        # Calculate the maximum possible scale values so that the
        # diagram width and height (respectively) fit the window.
        alloc = self.get_allocation()
        scaleX = float(alloc.width - 3) / width
        scaleY = float(alloc.height - 3) / height

        # Take the smaller scale, to make both with and height fit.
        if scaleX < scaleY:
            self.cvView.set_scale(scaleX)
        else:
            self.cvView.set_scale(scaleY)

    def scaleFitWidth(self):
        bounds = self.cvView.get_bounds()
        width, height = bounds.x2 - bounds.x1 + 1, bounds.y2 - bounds.y1 + 1

        # Calculate an initial scale value that uses the complete
        # window width, without a vertical scrollbar.
        alloc = self.get_allocation()
        scale = float(alloc.width) / width
        if scale * height > alloc.height:
            # The diagram doesn't fit vertically. Add ascrollbar.
            self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)

            # Recalculate the scale based on the width of the actual
            # canvas (i.e., taking the scrollbar into account). Notice
            # that when the window proprtions are close to those of
            # the diagram, the scrollbar will be 100% full.
            alloc = self.cvView.get_allocation()
            scale = float(alloc.width) / width
        else:
            # The diagram fits completely in the window. No scrollbar
            # needed.
            self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)

        self.cvView.set_scale(scale)

    def scaleFitHeight(self):
        # This method is symmetric to scaleFitWidth. See the comments
        # there for details.

        bounds = self.cvView.get_bounds()
        width, height = bounds.x2 - bounds.x1 + 1, bounds.y2 - bounds.y1 + 1

        alloc = self.get_allocation()
        scale = float(alloc.height) / height
        if scale * width > alloc.width:
            self.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_NEVER)

            alloc = self.cvView.get_allocation()
            scale = float(alloc.height) / height
        else:
            self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)

        self.cvView.set_scale(scale)

    def on__size_allocate(self, window, alloc):
        self._refreshScale()


    #
    # Tools
    #

    @signalTask
    def doDragScroll(self, event):
        release = WaitForSignal(self, 'button-release-event')
        move = WaitForSignal(self, 'motion-notify-event')

        # Find the canvas coordinates of the window's top left corner.
        # FIXME: GooCanvas should provide this service.
        b = self.cvView.get_bounds()
        ha, va = self.get_hadjustment(), self.get_vadjustment()
        cornerX = (b.x2 - b.x1) * (ha.value - ha.lower) / \
                  (ha.upper - ha.lower) + b.x1
        cornerY = (b.y2 - b.y1) * (va.value - va.lower) / \
                  (va.upper - va.lower) + b.y1

        # Save the position where the mouse button was originally
        # pressed.
        xi, yi = self.cvView.convert_from_pixels(event.x, event.y)
        xir, yir = event.x_root, event.y_root

        self.cvView.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.CIRCLE))

        yield (move, release)
        tEvent = get_event()
        while tEvent is not release:
            # The root coordinates in the event structure are often
            # outdated, specially when displaying large or complex
            # diagrams. Getting the current pointer position works
            # much better.
            (scr, xr, yr, mod) = self.get_display().get_pointer()

            # (xDesp, yDesp) is a vector telling us how the cursor
            # moved from its original position. It is expressed in
            # canvas coordinates.
            xrw, yrw = self.cvView.convert_from_pixels(xr, yr)
            xirw, yirw = self.cvView.convert_from_pixels(xir, yir)
            xDesp, yDesp = xrw - xirw, yrw - yirw

            self.cvView.scroll_to(cornerX - xDesp, cornerY - yDesp)

            yield (move, release)
            tEvent = get_event()

        self.cvView.window.set_cursor(self.TOOL_DRAG_SCROLL[1])

    TOOL_DRAG_SCROLL = (doDragScroll, gtk.gdk.Cursor(gtk.gdk.DOT))

    # The 'operate' tool just lets events flow to the canvas (and thus
    # to the canvas items).
    TOOL_OPERATE = (None, None)

    def setTool(self, tool):
        """Set the canvas' active tool.

        `tool` must be one of the `TOOL_*` constants in this class.
        """
        self.currentToolAction, cursor = tool
        self.cvView.window.set_cursor(cursor)

    def on_canvas__button_press_event(self, widget, event):
        # Start the current tool.
        if self.currentToolAction is not None:
            self.currentToolAction(self, event)
            return True
        else:
            return False
