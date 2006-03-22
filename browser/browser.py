#!/usr/bin/env python

import os, gtk
from SimpleGladeApp import SimpleGladeApp

glade_dir = ""

import string

import MySQLdb

from expression import uri, blanknode, literal
import modelfactory

import prefixes
import schema


class SchemaBrowser(SimpleGladeApp):
    def __init__(self, glade_path="browser.glade", root="schemaBrowser",
                 domain=None):
        glade_path = os.path.join(glade_dir, glade_path)
        SimpleGladeApp.__init__(self, glade_path, root, domain)

    def new(self):
        self.mainWindow = None

        # Set up the class browser.
        self.nodeCol = gtk.TreeViewColumn('Classes')
        self.classView.append_column(self.nodeCol)

        self.nodeCell = gtk.CellRendererText()
        self.nodeCol.pack_start(self.nodeCell, True)
        self.nodeCol.add_attribute(self.nodeCell, 'text', 1)
        self.nodeCol.set_sort_column_id(1)

        self.classTS = None

        # The class browser's popup menu.
        self.classPopUp = Menu1()
        self.classPopUp.browser = self
        self.classPopUp.mainWindow = None

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
        self.classPopUp.mainWindow = mainWindow

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

    def on_main_delete_event(self, widget, *args):
        self.hide()
        return True

    def on_classView_cursor_changed(self, widget, *args):
        if self.classTS == None:
            return

        cls = self.getCurrentClass()

        self.propertyLS = gtk.ListStore(object, str, str)
    
        for p in cls.properties:
            for r in p.range:
                self.propertyLS.append([p, str(p), str(r)])

        self.propertyView.set_model(self.propertyLS)

    def on_classView_drag_data_get(self, widget, context, selection,
                                   targetType, eventTime):
        cls = self.getCurrentClass()
        selection.set(selection.target, 8, str(cls))

    def on_classView_button_press_event(self, widget, event):
        if event.button == 3:
            self.classPopUp.main_widget.popup( None, None, None,
                                               event.button, event.time)


class MainWindow(SimpleGladeApp):
    def __init__(self, glade_path="browser.glade", root="mainWindow",
                 domain=None):
        glade_path = os.path.join(glade_dir, glade_path)
        SimpleGladeApp.__init__(self, glade_path, root, domain)

    def new(self):
        self.schemaBrowser = SchemaBrowser()
        self.schemaBrowser.setMainWindow(self)

        self.appName = self.main_widget.get_title()

        self.model = None
        self.resultLS = None

        # Allow dragging from the query result.
        self.resultsView.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK,
            [('text/plain', 0, 0)],
            gtk.gdk.ACTION_COPY)

    def openModel(self):
        connection = MySQLdb.connect(host='localhost', db='v-modell',
                                     read_default_group='client')

        prefixes = {
            'ex': 'http://example.com/model#'
            }

        self.model = modelfactory.getModel('SingleVersion', connection,
                                           prefixes, versionId=1)
        basename = 'V-Modell'

        #self.schemaBrowser.setSchema(schema.RdfSchema(self.model))

        self.main_widget.set_title("%s - %s" % (basename, self.appName))
        self.showMessage("Model '%s' opened succesfully." % basename)

    def showResults(self):
        """Show the results list in the window."""
        self.messageVBox.hide()
        self.resultsScrolled.show()

    def showMessage(self, msg):
        """Show the message text in the window and display the specified
        message."""
        self.messageView.get_buffer().set_text(msg)
        self.resultsScrolled.hide()
        self.messageVBox.show()

    def runQuery(self, queryString=None):
        if self.model == None:
            return

        buffer = self.queryText.get_buffer()
        if queryString == None:
            # Retrieve the query text from the window.
            queryString = buffer.get_text(buffer.get_start_iter(),
                                          buffer.get_end_iter())
        else:
            # Set the window to show the given query.
            buffer.set_text(queryString)

        # Run the query.
        try:
            results = self.model.query('SerQL', queryString)
        except Exception, e:
            self.showMessage("Error: %s" % str(e))
            return

        self.showBindingsResults(results)

    @staticmethod
    def nodeToStr(node):
        if isinstance(node, uri.Uri):
            return '<%s>' % prefixes.shortenUri(node)
        elif isinstance(node, blanknode.BlankNode):
            return 'bnode:%s' % node
        elif isinstance(node, literal.Literal):
            return '"%s"' % str(node.value)[:100]
        else:
            return "???"

    def showBindingsResults(self, results):
        """Display the query results object as table."""
        # Create a list store for the results:

        # Create the list store. All columns contain strings.
        self.resultLS = gtk.ListStore(*([str] * len(results.columnNames)))

#         if len(results) == 0:
#             self.showMessage("No results found")
#             return

        # Move the query results to the list store.
        for result in results:
            self.resultLS.append([self.nodeToStr(node)
                                  for node in result])

        # Disconect the view from its old model (we don't want any
        # funny repainting.)
        self.resultsView.set_model(None)

        # Get rid of the old columns in the results view.
        for col in self.resultsView.get_columns():
            self.resultsView.remove_column(col)

        # Add new columns for the new results.
        pos = 0
        for name in results.columnNames:
            # Create the column.
            col = gtk.TreeViewColumn(name)
            self.resultsView.append_column(col)

            # Add a text cell renderer.
            cell = gtk.CellRendererText()
            col.pack_start(cell, True)
            col.add_attribute(cell, 'text', pos)
            col.set_sort_column_id(pos)

            pos += 1

        # Set the new model.
        self.resultsView.set_model(self.resultLS)

        # Show the results view.
        self.showResults()

    def finalize(self):
        self.schemaBrowser.hide()
        gtk.main_quit()

    def on_mainWindow_delete_event(self, widget, *args):
        self.finalize()
        return False

    def on_open_activate(self, widget, *args):
        self.openModel()

    def on_quit_activate(self, widget, *args):
        self.finalize()

    def on_viewSchema_activate(self, widget, *args):
        self.schemaBrowser.show()

    def on_about_activate(self, widget, *args):
        print "on_about_activate called with self.%s" % widget.get_name()

    def on_clearButton_clicked(self, widget, *args):
        buffer = self.queryText.get_buffer()
        buffer.delete(buffer.get_start_iter(),
                      buffer.get_end_iter())

    def on_queryButton_clicked(self, widget, *args):
        self.runQuery()

    def on_resultsView_drag_data_get(self, widget, context, selection,
                                     targetType, eventTime):
        (path, col) = self.resultsView.get_cursor()
        tItr = self.resultLS.get_iter(path)
        entries = self.resultLS.get(tItr, *range(self. \
                                                 resultLS.get_n_columns()))
        selection.set(selection.target, 8, string.join(entries, ' '))


class Menu1(SimpleGladeApp):
    def __init__(self, glade_path="browser.glade", root="menu1", domain=None):
        glade_path = os.path.join(glade_dir, glade_path)
        SimpleGladeApp.__init__(self, glade_path, root, domain)

    def new(self):
        self.browser = None

    def on_queryInstances_activate(self, widget, *args):
        self.mainWindow.runQuery(
            "SELECT ?instance\nWHERE (?instance rdf:type %s)" % \
            self.browser.getCurrentClass())


def main():
    schema_browser = SchemaBrowser()
    main_window = MainWindow()
    main_window.openModel()
    menu1 = Menu1()

    schema_browser.run()

if __name__ == "__main__":
    main()
