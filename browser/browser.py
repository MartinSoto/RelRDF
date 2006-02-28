#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Python module browser.py
# Autogenerated from browser.glade
# Generated on Tue Apr  5 11:01:26 2005

# Warning: Do not delete or modify comments related to context
# They are required to keep user's code

import os, gtk
from SimpleGladeApp import SimpleGladeApp

glade_dir = ""

# Put your modules and data here

import string

import prefixes
import query
import schema


# From here through main() codegen inserts/updates a class for
# every top-level widget in the .glade file.

class SchemaBrowser(SimpleGladeApp):
    def __init__(self, glade_path="browser.glade", root="schemaBrowser", domain=None):
        glade_path = os.path.join(glade_dir, glade_path)
        SimpleGladeApp.__init__(self, glade_path, root, domain)

    def new(self):
        #context SchemaBrowser.new {
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

        #context SchemaBrowser.new }

    #context SchemaBrowser custom methods {

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

    #context SchemaBrowser custom methods }

    def on_main_delete_event(self, widget, *args):
        #context SchemaBrowser.on_main_delete_event {
        self.hide()
        return True
        #context SchemaBrowser.on_main_delete_event }

    def on_classView_cursor_changed(self, widget, *args):
        #context SchemaBrowser.on_classView_cursor_changed {
        if self.classTS == None:
            return

        cls = self.getCurrentClass()

        self.propertyLS = gtk.ListStore(object, str, str)
    
        for p in cls.properties:
            for r in p.range:
                self.propertyLS.append([p, str(p), str(r)])

        self.propertyView.set_model(self.propertyLS)
        #context SchemaBrowser.on_classView_cursor_changed }

    def on_classView_drag_data_get(self, widget, context, selection,
                                   targetType, eventTime):
        #context SchemaBrowser.on_classView_drag_data_get {
        cls = self.getCurrentClass()
        selection.set(selection.target, 8, str(cls))
        #context SchemaBrowser.on_classView_drag_data_get }

    def on_classView_button_press_event(self, widget, event):
        #context SchemaBrowser.on_classView_button_press_event {
        if event.button == 3:
            self.classPopUp.main_widget.popup( None, None, None,
                                               event.button, event.time)
        #context SchemaBrowser.on_classView_button_press_event }

class MainWindow(SimpleGladeApp):
    def __init__(self, glade_path="browser.glade", root="mainWindow", domain=None):
        glade_path = os.path.join(glade_dir, glade_path)
        SimpleGladeApp.__init__(self, glade_path, root, domain)

    def new(self):
        #context MainWindow.new {
        self.modelChooser = ModelFileChooser()
        self.modelChooser.setMainWindow(self)

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

        #context MainWindow.new }

    #context MainWindow custom methods {

    def openModel(self, fileName):
        basename = os.path.basename(fileName)

        try:
            self.model = query.Model(fileName)
        except Exception, e:
            self.showMessage("Error opening RDF model '%s': %s" % \
                             (fileName, str(e)))

        self.schemaBrowser.setSchema(schema.RdfSchema(self.model))

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
            results = self.model.query(queryString)
        except Exception, e:
            self.showMessage("Error: %s" % str(e))
            return

        if results.is_bindings():
            self.showBindingsResults(results)
        elif results.is_graph():
            pass
        else:
            if results.get_boolean():
                self.showMessage("True")
            else:
                self.showMessage("False")        

    def nodeToStr(node):
        if node.is_resource():
            return "%s" % prefixes.shortenUri(str(node.uri))
        elif node.is_literal():
            return '"%s"' % str(node)
        elif node.is_blank():
            return "(%s)" % node.blank_identifier
        else:
            return "???"
    nodeToStr = staticmethod(nodeToStr)

    def showBindingsResults(self, results):
        """Display the query results object as table."""
        assert results.is_bindings()

        # Create a list store for the results:

        # Retrieve the column names:
        columnNames = []
        for i in xrange(results.get_bindings_count()):
            columnNames.append(results.get_binding_name(i))

        # Create the list store. All columns contain strings.
        self.resultLS = gtk.ListStore(*([str] * len(columnNames)))

        if len(results) == 0:
            self.showMessage("No results found")
            return

        # Move the query results to the list store.
        for result in results:
            self.resultLS.append([self.nodeToStr(result[var])
                                  for var in columnNames])

        # Disconect the view from its old model (we don't want any
        # funny repainting.)
        self.resultsView.set_model(None)

        # Get rid of the old columns in the results view.
        for col in self.resultsView.get_columns():
            self.resultsView.remove_column(col)

        # Add new columns for the new results.
        pos = 0
        for name in columnNames:
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

    #context MainWindow custom methods }

    def on_mainWindow_delete_event(self, widget, *args):
        #context MainWindow.on_mainWindow_delete_event {
        self.finalize()
        return False
        #context MainWindow.on_mainWindow_delete_event }

    def on_open_activate(self, widget, *args):
        #context MainWindow.on_open_activate {
        self.modelChooser.show()
        #context MainWindow.on_open_activate }

    def on_quit_activate(self, widget, *args):
        #context MainWindow.on_quit_activate {
        self.finalize()
        #context MainWindow.on_quit_activate }

    def on_viewSchema_activate(self, widget, *args):
        #context MainWindow.on_viewSchema_activate {
        self.schemaBrowser.show()
        #context MainWindow.on_viewSchema_activate }

    def on_about_activate(self, widget, *args):
        #context MainWindow.on_about_activate {
        print "on_about_activate called with self.%s" % widget.get_name()
        #context MainWindow.on_about_activate }

    def on_clearButton_clicked(self, widget, *args):
        #context MainWindow.on_clearButton_clicked {
        buffer = self.queryText.get_buffer()
        buffer.delete(buffer.get_start_iter(),
                      buffer.get_end_iter())
        #context MainWindow.on_clearButton_clicked }

    def on_queryButton_clicked(self, widget, *args):
        #context MainWindow.on_queryButton_clicked {
        self.runQuery()
        #context MainWindow.on_queryButton_clicked }

    def on_resultsView_drag_data_get(self, widget, context, selection,
                                     targetType, eventTime):
        #context MainWindow.on_resultsView_drag_data_get {
        (path, col) = self.resultsView.get_cursor()
        tItr = self.resultLS.get_iter(path)
        entries = self.resultLS.get(tItr, *range(self. \
                                                 resultLS.get_n_columns()))
        selection.set(selection.target, 8, string.join(entries, ' '))
        #context MainWindow.on_resultsView_drag_data_get }

class ModelFileChooser(SimpleGladeApp):
    def __init__(self, glade_path="browser.glade", root="modelFileChooser", domain=None):
        glade_path = os.path.join(glade_dir, glade_path)
        SimpleGladeApp.__init__(self, glade_path, root, domain)

    def new(self):
        #context ModelFileChooser.new {
        self.mainWindow = None

        # Define some filters.
        filter = gtk.FileFilter()
        filter.set_name("RDF XML files")
        filter.add_pattern("*.rdf")
        filter.add_pattern("*.kaon")
        filter.add_pattern("*.owl")
        self.main_widget.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("Generic XML files")
        filter.add_pattern("*.xml")
        self.main_widget.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        self.main_widget.add_filter(filter)
        #context ModelFileChooser.new }

    #context ModelFileChooser custom methods {

    def setMainWindow(self, mainWindow):
        self.mainWindow = mainWindow

    #context ModelFileChooser custom methods }

    def on_modelChooserCancel_clicked(self, widget, *args):
        #context ModelFileChooser.on_modelChooserCancel_clicked {
        self.hide()
        #context ModelFileChooser.on_modelChooserCancel_clicked }

    def on_modelChooserOpen_clicked(self, widget, *args):
        #context ModelFileChooser.on_modelChooserOpen_clicked {
        self.hide()
        self.mainWindow.openModel(self.main_widget.get_filename())
        #context ModelFileChooser.on_modelChooserOpen_clicked }

class Menu1(SimpleGladeApp):
    def __init__(self, glade_path="browser.glade", root="menu1", domain=None):
        glade_path = os.path.join(glade_dir, glade_path)
        SimpleGladeApp.__init__(self, glade_path, root, domain)

    def new(self):
        #context Menu1.new {
        self.browser = None
        #context Menu1.new }

    #context Menu1 custom methods {

    #context Menu1 custom methods }

    def on_queryInstances_activate(self, widget, *args):
        #context Menu1.on_queryInstances_activate {
        self.mainWindow.runQuery(
            "SELECT ?instance\nWHERE (?instance rdf:type %s)" % \
            self.browser.getCurrentClass())
        #context Menu1.on_queryInstances_activate }

def main():
    schema_browser = SchemaBrowser()
    main_window = MainWindow()
    model_file_chooser = ModelFileChooser()
    menu1 = Menu1()

    schema_browser.run()

if __name__ == "__main__":
    main()