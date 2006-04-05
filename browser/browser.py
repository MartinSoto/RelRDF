#!/usr/bin/env python

import sys
import os

import gtk
import pango

from SimpleGladeApp import SimpleGladeApp

glade_dir = ""

import string

import MySQLdb

from expression import uri, blanknode, literal
import modelfactory

import prefixes
import schema
from schemapane import SchemaBrowser


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

        # Set a default query.
        self.queryText.get_buffer().set_text("select s, p, o\nfrom {s} p {o}")

        # Allow dragging from the query result.
        self.resultsView.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK,
            [('text/plain', 0, 0)],
            gtk.gdk.ACTION_COPY)

    def openModel(self, host, db):
        connection = MySQLdb.connect(host=host, db=db,
                                     read_default_group='client')

        self.model = modelfactory.getModel('SingleVersion', connection,
                                           prefixes.namespaces, versionId=1)
        basename = 'V-Modell'

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
            results = self.model.query('SerQL', queryString)
        except Exception, e:
            self.showMessage("Error: %s" % str(e))
            return

        self.showBindingsResults(results)

    @staticmethod
    def nodeToStr(node):
        if isinstance(node, uri.Uri):
            return prefixes.shortenUri(node)
        elif isinstance(node, blanknode.BlankNode):
            return 'bnode:%s' % node
        elif isinstance(node, literal.Literal):
            return '"%s"' % str(node.value)
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
            col.set_resizable(True)
            col.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
            self.resultsView.append_column(col)

            # Add a text cell renderer.
            cell = gtk.CellRendererText()
            cell.set_property('ellipsize', pango.ELLIPSIZE_END)
            cell.set_property('editable', True)
            cell.set_property('width-chars', 50)
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


if __name__ == "__main__":
    try:
        host, db = sys.argv[1:]
    except:
        print >> sys.stderr, 'usage: browser <host> <database>'
        sys.exit(1)

    schema_browser = SchemaBrowser()
    main_window = MainWindow()
    main_window.openModel(host, db)

    schema_browser.run()
