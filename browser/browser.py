#!/usr/bin/env python

import sys
import os
import string

import gtk
import pango

from kiwifixes import UiManagerDelegate
from kiwi.ui.delegates import Delegate, SlaveDelegate

import relrdf
from relrdf.expression import uri, blanknode, literal
from relrdf import commonns
from relrdf.util import nsshortener

import schema
from schemapane import SchemaBrowser
from queryeditor import QueryEditor


class MainWindow(UiManagerDelegate):
    """Main browser window."""

    mainGroup__actions = [('fileAction', None, _('_File'), None, None),
                          ('quitAction', gtk.STOCK_QUIT, None, None, None),
                          ('viewAction', None, _('_View'), None, None)]

    mainGroup__toggleActions = [('viewSideBarAction', None, _('_Side Bar'),
                                 'F9', None, None, True)]

    queryGroup__actions = [('executeQueryAction', gtk.STOCK_EXECUTE,
                            None, None, _('Execute the query')),
                           ('backwardHistoryAction', gtk.STOCK_GO_BACK,
                            None, None, _('Go to previous query in history')),
                           ('forwardHistoryAction', gtk.STOCK_GO_FORWARD,
                            None, None, _('Go to next query in history')),]

    uiDefinition = '''<ui>
    <menubar name="menuBar">
      <menu action="fileAction">
        <menuitem action="quitAction"/>
      </menu>
      <menu action="viewAction">
        <menuitem action="viewSideBarAction"/>
      </menu>
    </menubar>

    <toolbar name="queryToolbar">
      <toolitem action="backwardHistoryAction"/>
      <toolitem action="forwardHistoryAction"/>
      <separator/>
      <toolitem action="executeQueryAction"/>
    </toolbar>
    </ui>'''

    def __init__(self):
        UiManagerDelegate.__init__(self, gladefile="browser",
                                   toplevel_name='mainWindow')

        # Give the window a reasonable minimum size.
        self.toplevel.set_size_request(480, 360)

        # Set the initial dimensions of the window to 75% of the screen.
        (rootWidth, rootHeight) = \
                    self.toplevel.get_root_window().get_geometry()[2:4]
        self.toplevel.set_default_size(int(rootWidth * 0.85),
                                       int(rootHeight * 0.85))

        # Add the accelerator group to the toplevel window
        accelgroup = self.uiManager.get_accel_group()
        self.toplevel.add_accel_group(accelgroup)

        self.schemaBrowser = SchemaBrowser()
        self.schemaBrowser.setMainWindow(self)
        self.attach_slave('sidePane', self.schemaBrowser)

        menu = self.uiManager.get_widget('/menuBar')
        menuSlave = SlaveDelegate(toplevel=menu)
        self.attach_slave('menuBar', menuSlave)

        queryToolbar = self.uiManager.get_widget('/queryToolbar')
        queryToolbar.set_show_arrow(False)
        queryToolbar.set_style(gtk.TOOLBAR_ICONS)
        queryToolbar.set_tooltips(True)
        queryToolbarSlave = SlaveDelegate(toplevel=queryToolbar)
        self.attach_slave('queryToolbar', queryToolbarSlave)

        self.appName = self.mainWindow.get_title()

        self.model = None
        self.resultLS = None

        # Create the query editor:

        # We need to create the scrolled window by hand, because
        # Gazpacho insists on adding a viewport, and that prevents the
        # text view's scrolling features from working.
        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.show()

        self.queryEditor = QueryEditor()
        self.queryEditor.show()
        scrolled.add(self.queryEditor)
        
        editorSlave = SlaveDelegate(toplevel=scrolled)
        self.attach_slave('queryEditorPlaceholder', editorSlave)

        # Allow dragging from the query result.
        self.resultsView.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK,
            [('text/plain', 0, 0)],
            gtk.gdk.ACTION_COPY)

        # The history of executed queries.
        self.history = []

        # Current position in the history.
        self.historyPos = 0

        # Maximum number of queries that can be stored in the history.
        self.maxHistorySize = 100

        # We set, but do not execute an initial query.
        self._addToHistory("select ?g ?s ?p ?o\n"
                           "where { graph ?g {?s ?p ?o} }\n")

        # Initialize the results status bar.
        self._statusInit()


    #
    # RDF Model Management
    #

    _baseNs = {
        'rdf': commonns.rdf,
        'rdfs': commonns.rdfs,
        'relrdf': commonns.relrdf
     }

    def openModel(self, modelBaseType, modelBaseArgs, modelType, modelArgs):
        modelBase = relrdf.getModelBase(modelBaseType, **modelBaseArgs)
        self.model = modelBase.getModel(modelType, **modelArgs)

        # Create an appropriate URI shortener.
        self.shortener = nsshortener.NamespaceUriShortener(shortFmt='%s:%s',
                                                           longFmt='<%s>')
        self.shortener.addPrefix('rdf', commonns.rdf)
        self.shortener.addPrefix('rdfs', commonns.rdfs)
        self.shortener.addPrefix('relrdf', commonns.relrdf)

        # Add the namespaces from the model.
        self.shortener.addPrefixes(self.model.getPrefixes())

        self.schemaBrowser.setSchema(schema.RdfSchema(self.model),
                                     self.shortener)

        self.mainWindow.set_title("%s - %s" % (db, self.appName))
        self.showMessage("Model '%s' opened succesfully." % db)


    #
    # Query Execution and History
    #

    def runQuery(self, queryString):
        """Execute a query."""

        if self.model == None:
            return

        self._addToHistory(queryString)

        # Run the query.
        try:
            results = self.model.query('SPARQL', queryString)
        except relrdf.PositionError, e:
            self.queryEditor.markErrorExtents(e.extents)
            self.showMessage("Error: %s" % e.msg)
            return
        except relrdf.Error, e:
            self.showMessage("Error: %s" % str(e))
            return

        self.showResults(results)

    def backwardHistory(self):
        if self.historyPos == 0:
            return

        self.history[self.historyPos] = self.queryEditor.getQueryString()
        self.historyPos -= 1
        self._updateHistoryState()

    def forwardHistory(self):
        if self.historyPos >= len(self.history) - 1:
            return
        
        self.history[self.historyPos] = self.queryEditor.getQueryString()
        self.historyPos += 1
        self._updateHistoryState()
        
    def _addToHistory(self, queryString):
        # Do not store repeated queries.
        try:
            self.history.remove(queryString)
        except ValueError:
            pass

        while len(self.history) > self.maxHistorySize - 1:
            self.history.pop(0)

        self.history.append(queryString)
        self.historyPos = len(self.history) - 1
        self._updateHistoryState()

    def _updateHistoryState(self):
        # Don't touch the editor if it isn't strictly
        # necessary. Changing the state may affect things like the
        # cursor position and undo history.
        if self.queryEditor.getQueryString() != \
               self.history[self.historyPos]:
            self.queryEditor.setQueryString(self.history[self.historyPos])

        self.backwardHistoryAction.set_sensitive(self.historyPos > 0)
        self.forwardHistoryAction.set_sensitive(self.historyPos <
                                                len(self.history) - 1)


    #
    # Results Display
    #

    def showMessage(self, msg):
        """Show the message text in the window and display the specified
        message."""
        self.messageView.get_buffer().set_text(msg)
        self.resultsScrolled.hide()
        self.messageVBox.show()
        self.hideResultCount()

    def nodeToStr(self, node):
        if isinstance(node, uri.Uri):
            return self.shortener.shortenUri(node)
        elif isinstance(node, blanknode.BlankNode):
            return 'bnode:%s' % node
        elif isinstance(node, literal.Literal):
            return '"%s"' % str(node.value)
        else:
            return "???"

    def showResults(self, results):
        """Display the query results object as table."""
        # Create a list store for the results:

        # Create the list store. All columns contain strings.
        self.resultLS = gtk.ListStore(*([str] * len(results.columnNames)))

        if len(results) == 0:
            self.showMessage(_("No results found"))
            return

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
        self.messageVBox.hide()
        self.resultsScrolled.show()

        # Display the result count.
        self.showResultCount(len(results))

    #
    # Results Status Bar
    #

    def _statusInit(self):
        self._baseStatusCtx = self.resultsStatus.get_context_id('base')
        self._resultCountStatusCtx = \
            self.resultsStatus.get_context_id('count')
        self.resultsStatus.push(self._baseStatusCtx, _('No results shown'))

    def showResultCount(self, count):
        self.resultsStatus.push(self._resultCountStatusCtx,
                                _('%d result(s) shown') % count)

    def hideResultCount(self):
        self.resultsStatus.pop(self._resultCountStatusCtx)


    #
    # Event Handling
    #


    def finalize(self):
        gtk.main_quit()

    def on_mainPaned__realize(self, widget, *args):
        # Give the left pane a reazonable size.
        self.mainPaned.set_position(int(self.mainPaned.\
                                        get_property('max-position') * 0.3))

    def on_mainWindow__delete_event(self, widget, *args):
        self.finalize()
        return False

    def on_quitAction__activate(self, widget, *args):
        self.finalize()

    def on_executeQueryAction__activate(self, widget, *args):
        self.runQuery(self.queryEditor.getQueryString())

    def on_backwardHistoryAction__activate(self, widget, *args):
        self.backwardHistory()

    def on_forwardHistoryAction__activate(self, widget, *args):
        self.forwardHistory()

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

