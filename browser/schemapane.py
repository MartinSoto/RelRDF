import os

import gtk

from kiwi.ui.delegates import Delegate


class SchemaBrowser(Delegate):
    def __init__(self):
        Delegate.__init__(self, gladefile="browser",
                          toplevel_name='schemaBrowser')

        self.mainWindow = None

        # Set up the class browser.
        self.nodeCol = gtk.TreeViewColumn('Classes')
        self.classView.append_column(self.nodeCol)

        self.nodeCell = gtk.CellRendererText()
        self.nodeCol.pack_start(self.nodeCell, True)
        self.nodeCol.add_attribute(self.nodeCell, 'text', 1)
        self.nodeCol.set_sort_column_id(1)

        self.classTS = None

#         # The class browser's popup menu.
#         self.classPopUp = Menu1()
#         self.classPopUp.browser = self
#         self.classPopUp.mainWindow = None

        # Set up the property browser.
        self.propNameCol = gtk.TreeViewColumn('Property')
        self.propertyView.append_column(self.propNameCol)
        self.rangeCol = gtk.TreeViewColumn('Range')
        self.propertyView.append_column(self.rangeCol)

        self.propNameCell = gtk.CellRendererText()
        self.propNameCol.pack_start(self.propNameCell, True)
        self.propNameCol.add_attribute(self.propNameCell, 'text', 1)
        self.propNameCol.set_sort_column_id(1)

        self.rangeCell = gtk.CellRendererText()
        self.rangeCol.pack_end(self.rangeCell, True)
        self.rangeCol.add_attribute(self.rangeCell, 'text', 2)
        self.rangeCol.set_sort_column_id(2)

        self.propertyLS = gtk.ListStore(object, str, str)
        self.propertyView.set_model(self.propertyLS)

        # Allow dragging from the class view.
        self.classView.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK,
            [('text/plain', 0, 0)],
            gtk.gdk.ACTION_COPY)

    def setMainWindow(self, mainWindow):
        self.mainWindow = mainWindow
        #self.classPopUp.mainWindow = mainWindow

    def setSchema(self, sch):
        self.schema = sch

        self.classTS = gtk.TreeStore(object, str)

        for cls in self.schema.classes.values():
            if len(cls.ancestors) == 0:
                self.addRdfClass(cls)

        self.classView.set_model(self.classTS)
        self.classView.expand_all()

    def addRdfClass(self, rdfClass, parent=None):
        newParent = self.classTS. \
                    append(parent,
                           [rdfClass, str(rdfClass)])

        for d in rdfClass.descendants:
            self.addRdfClass(d, newParent)

    def getCurrentClass(self):
        (path, col) = self.classView.get_cursor()
        tItr = self.classTS.get_iter(path)
        (cls,) = self.classTS.get(tItr, 0)
        return cls

    def on_schemaBrowser__delete_event(self, widget, *args):
        self.hide()
        return True

    def on_classView__cursor_changed(self, widget, *args):
        if self.classTS == None:
            return

        cls = self.getCurrentClass()

        self.propertyLS = gtk.ListStore(object, str, str)
    
        for p in cls.properties:
            for r in p.range:
                self.propertyLS.append([p, str(p), str(r)])

        self.propertyView.set_model(self.propertyLS)

    def on_classView__drag_data_get(self, widget, context, selection,
                                   targetType, eventTime):
        cls = self.getCurrentClass()
        selection.set(selection.target, 8, str(cls))

#     def on_classView_button_press_event(self, widget, event):
#         if event.button == 3:
#             self.classPopUp.main_widget.popup( None, None, None,
#                                                event.button, event.time)


# class Menu1(SimpleGladeApp):
#     def __init__(self, glade_path="browser.glade", root="menu1", domain=None):
#         glade_path = os.path.join(glade_dir, glade_path)
#         SimpleGladeApp.__init__(self, glade_path, root, domain)

#     def new(self):
#         self.browser = None

#     def on_queryInstances_activate(self, widget, *args):
#         self.mainWindow.runQuery(
#             "select instance\nfrom {instance} rdf:type {%s}" % \
#             self.browser.getCurrentClass())
