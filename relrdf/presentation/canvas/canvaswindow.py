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

import gtk

from canvaswidget import CanvasWidget

# Make glade files available to Kiwi.
from relrdf.presentation import gladefiles

from relrdf.presentation.kiwifixes import UiManagerDelegate
from kiwi.ui.delegates import SlaveDelegate


class CanvasWindow(UiManagerDelegate):
    """Diagram canvas window."""

    # These two fields must be kept synchronized.
    mainGroup__radioActions_tool = [0,
                                    ('toolOperate', None, _('_O'),
                                     None, _('Operate on diagram elements'),
                                     0),
                                    ('toolGrabScroll', None, _('_S'),
                                     None, _('Grab & scroll'),
                                     1),]
    _tools = [CanvasWidget.TOOL_OPERATE,
              CanvasWidget.TOOL_DRAG_SCROLL,]


    uiDefinition = '''<ui>
    <toolbar name="mainToolbar">
      <toolitem action="toolOperate"/>
      <toolitem action="toolGrabScroll"/>
    </toolbar>
    </ui>'''


    def __init__(self):
        UiManagerDelegate.__init__(self,
                                   gladefile='canvas.glade',
                                   toplevel_name='canvasWindow')

        # Give the window a reasonable minimum size.
        self.toplevel.set_size_request(480, 360)

        # Set the initial dimensions of the window to 75% of the screen.
        (rootWidth, rootHeight) = \
                    self.toplevel.get_root_window().get_geometry()[2:4]
        self.toplevel.set_default_size(int(rootWidth * 0.85),
                                       int(rootHeight * 0.85))

        # Add the accelerator group to the toplevel window.
        accelgroup = self.uiManager.get_accel_group()
        self.toplevel.add_accel_group(accelgroup)

        # Add the toolbar.
        mainToolbar = self.uiManager.get_widget('/mainToolbar')
        mainToolbar.set_show_arrow(False)
        mainToolbar.set_style(gtk.TOOLBAR_ICONS)
        mainToolbar.set_tooltips(True)
        mainToolbarSlave = SlaveDelegate(toplevel=mainToolbar)
        self.attach_slave('mainToolbar', mainToolbarSlave)

        # Integrate the canvas into the main window.
        self.canvasWidget = CanvasWidget()
        self.canvasWidget.show()
        canvasSlave = SlaveDelegate(toplevel=self.canvasWidget)
        self.attach_slave('canvasWidget', canvasSlave)

        # Setup the scale widget.
        # FIXME: Glade inserts a blank line at the beginning.
        self.scaleCombo.remove_text(0)
        for text, method, args in self._scaleValues:
            self.scaleCombo.append_text(text)
        self.scaleCombo.set_row_separator_func(self._checkSeparator)

        # This operation indirectly calls the canvas' setScale method.
        self.scaleCombo.set_active(self._defaultScale)

        # FIXME: Layout works only if the window is displayed.
        self.show()

    def getCanvas(self):
        return self.canvasWidget.getCanvas()

    def getCanvasView(self):
        return self.canvasWidget.getCanvasView()


    #
    # Scale Control
    #

    _scaleValues = (
       (_('Best Fit'), CanvasWidget.scaleBestFit, ()),
       (_('Fit Width'), CanvasWidget.scaleFitWidth, ()),
       (_('Fit Height'), CanvasWidget.scaleFitHeight, ()),
       ('---', None, None),
       (_('25%'), CanvasWidget.scalePercent, (25,)),
       (_('50%'), CanvasWidget.scalePercent, (50,)),
       (_('75%'), CanvasWidget.scalePercent, (75,)),
       (_('100%'), CanvasWidget.scalePercent, (100,)),
       (_('125%'), CanvasWidget.scalePercent, (125,)),
       (_('150%'), CanvasWidget.scalePercent, (150,)),
       (_('175%'), CanvasWidget.scalePercent, (175,)),
       (_('200%'), CanvasWidget.scalePercent, (200,)),
       (_('300%'), CanvasWidget.scalePercent, (300,)),
       (_('400%'), CanvasWidget.scalePercent, (400,)),
       )

    # Row number for the default scale value.
    _defaultScale = 5

    def _checkSeparator(self, model, itr):
        # If there is no associated method, this is a separator.
        return self._scaleValues[self.scaleCombo.get_model(). \
                                 get_path(itr)[0]][1] is None

    def on_scaleCombo__changed(self, combo):
        text, method, args = self._scaleValues[combo.get_active()]
        self.canvasWidget.setScale(method, *args)


    #
    # Tool Selection
    #

    def on_toolOperate__changed(self, widget, current):
        self.canvasWidget.setTool(self._tools[widget.get_current_value()])


    #
    # Finalization
    #

    def finalize(self):
        gtk.main_quit()

    def on_canvasWindow__delete_event(self, window, *args):
        self.finalize()
        return False


if __name__ == "__main__":
    import pango
    import goocanvas

    canvasWin = CanvasWindow()
    canvas, view = canvasWin.getCanvas(), canvasWin.getCanvasView()

    root = canvas.get_root_item()
    view.set_bounds(-500, -500, 500, 500)

    border = goocanvas.Rect(x=-500, y=-500, width=1000, height=1000,
                            line_width=5, stroke_color='blue',
                            fill_color='red')
    root.add_child(border)

    r = goocanvas.Rect(x=-400, y=-400, width=800, height=800,
                       line_width=20, fill_color='white')
    root.add_child(r)

    def buttonPress(view, targetView, event):
        print 'Button press: %d, %d' % (event.x, event.y)
    rv = view.get_item_view(r)
    rv.connect('button-press-event', buttonPress)

    message = "Lorem ipsum dolor sit amet, consectetuer adipiscing elit. " \
              "Maecenas pulvinar. Mauris auctor congue nibh. Nullam at " \
              "leo. Curabitur sit amet ligula ac lorem consequat mollis."
    text = goocanvas.Text(text=message,
                          x=0, y=0,
                          anchor=gtk.ANCHOR_CENTER,
                          font="Sans 40",
                          alignment=pango.ALIGN_CENTER,
                          use_markup=True,
                          width=600,
                          fill_color="black")
    root.add_child(text)

    #root.rotate(45, 0, 0)

    gtk.main()

