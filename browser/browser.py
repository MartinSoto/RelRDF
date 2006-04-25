#!/usr/bin/env python

import sys
import os
import string

import gtk
import pango

from kiwifixes import UiManagerDelegate
from kiwi.ui.delegates import Delegate, SlaveDelegate

from relrdf.expression import uri, blanknode, literal
import relrdf

import prefixes
import schema
from schemapane import SchemaBrowser


class MainWindow(UiManagerDelegate):
    """Main browser window."""

    mainGroup__actions = [('fileAction', None, _('_File'), None, None),
                          ('quitAction', gtk.STOCK_QUIT, None, None, None),
                          ('viewAction', None, _('_View'), None, None)]

    mainGroup__toggleActions = [('viewSideBarAction', None, _('_Side Bar'),
                                 'F9', None, None, True)]

    uiDefinition = '''<ui>
    <menubar name="menuBar">
      <menu action="fileAction">
        <menuitem action="quitAction"/>
      </menu>
      <menu action="viewAction">
        <menuitem action="viewSideBarAction"/>
      </menu>
    </menubar>
    </ui>'''

    def __init__(self):
        UiManagerDelegate.__init__(self, gladefile="browser",
                                   toplevel_name='mainWindow')

        # Add the accelerator group to the toplevel window
        accelgroup = self.uiManager.get_accel_group()
        self.toplevel.add_accel_group(accelgroup)

        self.schemaBrowser = SchemaBrowser()
        self.schemaBrowser.setMainWindow(self)
        self.attach_slave('sidePane', self.schemaBrowser)

        menu = self.uiManager.get_widget('/menuBar')
        menuSlave = SlaveDelegate(toplevel=menu)
        self.attach_slave('menuBar', menuSlave)

        self.appName = self.mainWindow.get_title()

        self.model = None
        self.resultLS = None

        # Set a default query.
        self.queryText.get_buffer().set_text("select s, p, o\nfrom {s} p {o}")

        # Allow dragging from the query result.
        self.resultsView.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK,
            [('text/plain', 0, 0)],
            gtk.gdk.ACTION_COPY)

    def openModel(self, modelBaseType, modelBaseArgs, modelType, modelArgs):
        if not modelArgs.has_key('prefixes'):
            modelArgs['prefixes'] = prefixes.namespaces

        modelBase = relrdf.getModelBase(modelBaseType, **modelBaseArgs)
        self.model = modelBase.getModel(modelType, **modelArgs)

        self.schemaBrowser.setSchema(schema.RdfSchema(self.model))

        self.mainWindow.set_title("%s - %s" % (db, self.appName))
        self.showMessage("Model '%s' opened succesfully." % db)

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
        gtk.main_quit()

    def on_mainWindow__delete_event(self, widget, *args):
        self.finalize()
        return False

    def on_quitAction__activate(self, widget, *args):
        self.finalize()

    def on_clearButton__clicked(self, widget, *args):
        buffer = self.queryText.get_buffer()
        buffer.delete(buffer.get_start_iter(),
                      buffer.get_end_iter())

    def on_queryButton__clicked(self, widget, *args):
        self.runQuery()

    def on_resultsView__drag_data_get(self, widget, context, selection,
                                      targetType, eventTime):
        (path, col) = self.resultsView.get_cursor()
        tItr = self.resultLS.get_iter(path)
        entries = self.resultLS.get(tItr, *range(self. \
                                                 resultLS.get_n_columns()))
        selection.set(selection.target, 8, string.join(entries, ' '))

    def on_viewSideBarAction__toggled(self, action):
        if action.get_active():
            self.sidePane.show()
        else:
            self.sidePane.hide()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print >> sys.stderr, \
              'usage: browser <host> <database> <model type> [<model params>]'
        sys.exit(1)

    host, db, modelType = sys.argv[1:4]

    modelArgs = {}
    for arg in sys.argv[4:]:
        key, value = arg.split('=')
        modelArgs[key] = value

    main_window = MainWindow()
    main_window.openModel('mysql',
                          {'host': host, 'db': db,
                           'read_default_group': 'client'},
                          modelType, modelArgs)

    main_window.show()

    gtk.main()

