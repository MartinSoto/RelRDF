import os

import gtk

from kiwifixes import UiManagerSlaveDelegate

import pixmaps


class SchemaBrowser(UiManagerSlaveDelegate):

    popupGroup__actions = [('showInstances', None,
                            _('Show _Instances'), None, None)]

    uiDefinition = '''<ui>
    <popup name="classPopUp">
      <menuitem action="showInstances"/>
    </popup>
    </ui>'''

    def __init__(self):
        UiManagerSlaveDelegate.__init__(self, gladefile="browser",
                                        toplevel_name='schemaBrowser')
        self.mainWindow = None

        # Set up the class browser.
        self.nodeCol = gtk.TreeViewColumn(_('Schema'))
        self.classView.append_column(self.nodeCol)

        pixbufRenderer = gtk.CellRendererPixbuf()
        self.nodeCol.pack_start(pixbufRenderer, False)
        self.nodeCol.add_attribute(pixbufRenderer, 'pixbuf', 1)

        textRenderer = gtk.CellRendererText()
        self.nodeCol.pack_start(textRenderer, True)
        self.nodeCol.add_attribute(textRenderer, 'markup', 2)

        self.nodeCol.set_sort_column_id(1)

        self.classTS = None

        # The class browser's popup menu.
        self.classPopUp = self.uiManager.get_widget('/classPopUp')

        # Allow dragging from the class view.
        self.classView.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK,
            [('text/plain', 0, 0)],
            gtk.gdk.ACTION_COPY)

    def setMainWindow(self, mainWindow):
        self.mainWindow = mainWindow
        self.classPopUp.mainWindow = mainWindow

    def setSchema(self, sch):
        self.schema = sch

        self.classTS = gtk.TreeStore(object, gtk.gdk.Pixbuf, str)

        for cls in self.schema.classes.values():
            self.addRdfClass(cls)

        self.classView.set_model(self.classTS)

    def addRdfClass(self, rdfClass):
        parent = self.classTS. \
                 append(None, [rdfClass, pixmaps.classPixbuf,
                               '<b>%s</b>' % str(rdfClass)])

        for p in rdfClass.getAllProperties():
            for r in p.range:
                self.classTS.append(parent,
                                    [p, pixmaps.propertyPixbuf,
                                     '<b>%s</b> %s' % (str(p), str(r))])

    def getCurrentClass(self):
        (path, col) = self.classView.get_cursor()
        tItr = self.classTS.get_iter(path)
        (cls,) = self.classTS.get(tItr, 0)
        return cls

    def on_classView__drag_data_get(self, widget, context, selection,
                                   targetType, eventTime):
        cls = self.getCurrentClass()
        selection.set(selection.target, 8, str(cls))

    # FIXME: This should be button_press but something in
    # Kiwi/Gazpacho seems to be trapping the event.
    def on_classView__button_release_event(self, widget, event):
        if event.button == 3:
            self.classPopUp.popup(None, None, None,
                                  event.button, event.time)

    def on_showInstances__activate(self, widget, *args):
        self.mainWindow.runQuery(
            "select instance\nfrom {instance} rdf:type {%s}" % \
            self.getCurrentClass())
