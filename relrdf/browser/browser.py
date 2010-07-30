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


import sys
import string
import re
import textwrap
import time

import gtk
import gtk.glade
import gtk.gdk
import pango

from evolyzer.kiwifixes import UiManagerDelegate, UiManagerSlaveDelegate
from kiwi.ui.delegates import Delegate, SlaveDelegate
#import kiwi.environ.environ

import relrdf
from relrdf.expression import uri, literal
from relrdf import commonns
from relrdf.util import nsshortener

from evolyzer import gladefiles

from evolyzer.util.Config import getCFGFilename
from ConfigParser import ConfigParser
from evolyzer.util.modelselector import getObjectName
from evolyzer.util.modelselector import getModel as promptModel
from evolyzer.util import gtke
import evolyzer.icons

import schema
from schemapane import SchemaBrowser
from queryeditor import QueryEditor

import gobject
THREADING = True
gobject.threads_init()


def escape(s, escapeMap = None, addDefaults = True):
    defaultEscapeMap = {"\n":"n", "\r":"r", "\t":"t"}
    if escapeMap == None:
        if addDefaults:
            escapeMap = defaultEscapeMap
        else:
            return s # Nothing to do!
    elif addDefaults:
        escapeMap = dict(zip(escapeMap.keys() + defaultEscapeMap.keys(),
            escapeMap.values() + defaultEscapeMap.values()))
    s = s.replace("\\", "\\\\")
    for c in escapeMap:
        s = s.replace(c, "\\" + escapeMap[c])
    return s

def unescape(s, escapeMap = None, addDefaults = True):
    defaultEscapeMap = {"\n":"n", "\r":"r", "\t":"t", "\\":"\\"}
    if escapeMap == None:
        if addDefaults:
            escapeMap = defaultEscapeMap
        else:
            return s # Nothing to do!
    elif addDefaults:
        escapeMap = dict(zip(escapeMap.keys() + defaultEscapeMap.keys(),
            escapeMap.values() + defaultEscapeMap.values()))
    escapeMap = dict(zip(escapeMap.values(), escapeMap.keys()))
    return re.sub(r'\\(.)', lambda matchobj: escapeMap.get(matchobj.group(1), 
        "") , s)

def runBookmarkDialog(name, model, defaultParent=None, **kwargs):
    if defaultParent == None:
        defaultParent = model.get_iter_root()
    if getattr(runBookmarkDialog, "bookmarkDialog", None) == None:
        glade = gtk.glade.XML(gladefiles.gladefile("browser.glade"))
        runBookmarkDialog.bookmarkDialog = glade.get_widget("BookmarkDialog")
        gtke.staticConnect(glade.get_widget("BookmarkDialogOK"), "clicked",
            runBookmarkDialog.bookmarkDialog.response, gtk.RESPONSE_OK)
        gtke.staticConnect(glade.get_widget("BookmarkDialogCancel"), "clicked",
            runBookmarkDialog.bookmarkDialog.response, gtk.RESPONSE_CANCEL)
        runBookmarkDialog.bookmarkDialog.nameEntry =\
            glade.get_widget("BookmarkDialogNameEntry")
        gtke.staticConnect(runBookmarkDialog.bookmarkDialog.nameEntry,
            "activate", runBookmarkDialog.bookmarkDialog.response,
            gtk.RESPONSE_OK)
        runBookmarkDialog.bookmarkDialog.parentSelector =\
            glade.get_widget("BookmarkDialogParentSelector")
        cell = gtk.CellRendererText()
        runBookmarkDialog.bookmarkDialog.parentSelector.pack_start(cell, True)
        runBookmarkDialog.bookmarkDialog.parentSelector.add_attribute(cell,
            'text', 0)
    gtke.setProperties(runBookmarkDialog.bookmarkDialog, kwargs)
    runBookmarkDialog.bookmarkDialog.nameEntry.set_text(name)
    folderModel = model.filter_new()
    folderModel.set_visible_func(lambda model, iter: model.get_value(iter, 2)\
        == None)
    runBookmarkDialog.bookmarkDialog.parentSelector.set_model(folderModel)
    runBookmarkDialog.bookmarkDialog.parentSelector.set_active_iter(
        folderModel.convert_child_iter_to_iter(defaultParent))
    Result = runBookmarkDialog.bookmarkDialog.run()
    runBookmarkDialog.bookmarkDialog.hide()
    if Result == gtk.RESPONSE_OK:
        return (runBookmarkDialog.bookmarkDialog.nameEntry.get_text(),
            folderModel.convert_iter_to_child_iter(runBookmarkDialog.\
            bookmarkDialog.parentSelector.get_active_iter()))
    else:
        return (None, None)


class NotebookPage(UiManagerSlaveDelegate):
    queryGroup__actions = [('executeQueryAction', gtk.STOCK_EXECUTE,
                            None, None, _('Execute the query (Ctrl+Enter)')),
                           ('addBookmarkAction', gtk.STOCK_ADD,
                            None, None, _('Add query to bookmarked')),
                           ('backwardHistoryAction', gtk.STOCK_GO_BACK,
                            None, None, _('Go to previous query in history')),
                           ('showHistoryAction', gtk.STOCK_INDEX,
                            None, None, _('Show history list')),
                           ('forwardHistoryAction', gtk.STOCK_GO_FORWARD,
                            None, None, _('Go to next query in history')),]

    historyGroup__actions = [('deleteHistoryAction',
                              gtk.STOCK_DELETE,
                              None,
                              None,
                              _('Delete selected items from history list'))]
    historyGroup__toggleActions = [('multilineHistoryAction',
                                    gtk.STOCK_JUSTIFY_FILL,
                                    None,
                                    None,
                                    _('Show line breaks in history list')),
                                   ('singlelineHistoryAction',
                                    "icon-single-line",
                                     None, 
                                     None,
                                     _('Show single lines in history list'))]

    bookmarksGroup__actions = [('newBookmarkAction',
                                gtk.STOCK_NEW,
                                None,
                                None,
                                _('Add current Statement to Bookmarks')),
                               ('newFolderAction',
                                gtk.STOCK_DIRECTORY,
                                None,
                                None,
                                _('Create new Folder')),
                               ('deleteBookmarkAction',
                                gtk.STOCK_DELETE,
                                None,
                                None,
                                _('Delete Bookmark or Folder'))]
    
    uiDefinition = '''<ui>
    <toolbar name="queryToolbar">
      <toolitem action="backwardHistoryAction"/>
      <toolitem action="showHistoryAction"/>
      <toolitem action="forwardHistoryAction"/>
      <separator/>
      <toolitem action="addBookmarkAction"/>
      <separator/>
      <toolitem action="executeQueryAction"/>
    </toolbar>
    <toolbar name="sideToolbar">
      <separator/>
      <toolitem action="deleteHistoryAction"/>
      <toolitem action="singlelineHistoryAction"/>
      <toolitem action="multilineHistoryAction"/>
      <toolitem action="newBookmarkAction"/>
      <toolitem action="newFolderAction"/>
      <toolitem action="deleteBookmarkAction"/>
    </toolbar>
    </ui>'''
    
    sidepaneToolbars = ( # A list with one entry for each page of the sidepane.
                         # For each page contains a Toolbutton Class and
                         # its parameters
                        (),
                        (gtk.ToolButton,
                          {"name"    : "deleteHistoryAction",
                           "stock-id": gtk.STOCK_DELETE,
                           "tooltip" : "Delete selected items from history list"},
                         gtk.SeparatorToolItem,
                          {},
                         gtk.ToggleToolButton,
                          {"name"    : "singlelineHistoryAction",
                           "stock-id": "icon-single-line",
                           "tooltip" : "Show single lines in history list"},
                         gtk.ToggleToolButton,
                          {"name"    : "multilineHistoryAction",
                           "stock-id": gtk.STOCK_JUSTIFY_FILL,
                           "tooltip" : "Show line breaks in history list"}),
                        (gtk.ToolButton, 
                          {"name"    : "newBookmarksAction",
                           "stock-id": gtk.STOCK_NEW,
                           "tooltip" : "Add current statement to bookmarks"},
                         gtk.ToolButton,
                          {"name"    : "newFolderAction",
                           "stock-id": gtk.STOCK_DIRECTORY,
                           "tooltip" : "Create new folder"},
                         gtk.ToolButton, 
                          {"name"    : "deleteBookmarkAction", 
                           "stock-id": gtk.STOCK_DELETE,
                           "tooltip" : "Delete bookmark or folder"})
                       )

    def __init__(self):
        UiManagerSlaveDelegate.__init__(self, gladefile='browser.glade',
                                              toplevel_name='notebookPage')

        self.schemaBrowser = SchemaBrowser()
        self.schemaBrowser.setMainWindow(self)
        self.attach_slave('sidePane', self.schemaBrowser)
        
        queryToolbar = self.uiManager.get_widget('/queryToolbar')
        queryToolbar.set_show_arrow(False)
        queryToolbar.set_style(gtk.TOOLBAR_ICONS)
        queryToolbar.set_tooltips(True)
        queryToolbarSlave = SlaveDelegate(toplevel=queryToolbar)
        self.attach_slave('queryToolbar', queryToolbarSlave)

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

        # Button-Press-Event must be captured to retrieve Ctrl+Enter
        self.queryEditor.connect("key-press-event",
            self.queryEditor__key_press_event);

        self.queryEditor.show()
        scrolled.add(self.queryEditor)
        
        editorSlave = SlaveDelegate(toplevel=scrolled)
        self.attach_slave('queryEditorPlaceholder', editorSlave)

        # Allow dragging from the query result.
        self.resultsView.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK,
            [('text/plain', 0, 0)],
            gtk.gdk.ACTION_COPY)

        # Current position in the history.
        self.historyPos = 0

        # Maximum number of queries that can be stored in the history.
        self.maxHistorySize = 100
        
        # Maximum number of queries that are shown in the history menu.
        self.maxHistoryMenuSize = 100

        # The history of executed queries.
        self.multilineHistory = True
        self.historyFileName = getCFGFilename("evolyzer") + "query_history"
        self.historyTreeview = self.get_widget("HistoryTreeview")
        self.history = gtk.ListStore(str)
        self.historyTreeview.set_model(self.history)
        cr = gtk.CellRendererText()
        vol = gtk.TreeViewColumn(None, cr)
        vol.set_cell_data_func(cr, self.history_cell_needs_data)
        self.historyTreeview.append_column(vol)
        self.setMultiline(True)
        
        try:
            self.loadHistory(self.historyFileName)
            self.historyPos = 0
            self._updateHistoryState()
        except:
            # We set, but do not execute an initial query.
            #self.history = list()
            self._addToHistory("select ?s ?p ?o\n"
                               "where {\n  ?s ?p ?o\n}\n")

        #must be moved to openModel
        self.bookmarkFileName = getCFGFilename("evolyzer") + "bookmarks"
        self.bookmarkTreeview = self.get_widget("BookmarksTreeview")
        self.bookmarkStore = gtk.TreeStore(str, str, str) 
                                        # (name, STOCK_ID, command)
        self.bookmarkStore.append(None, ("All Bookmarks", gtk.STOCK_HOME, None))
        try:
            self.loadBookmarks(self.bookmarkFileName)
        except:
            pass
        
        self.bookmarkTreeview.set_model(self.bookmarkStore.filter_new(0))
        crText = gtk.CellRendererText()
        crIcon = gtk.CellRendererPixbuf()
        Column = gtk.TreeViewColumn("Bookmark")
        Column.pack_start(crIcon, False)
        Column.pack_start(crText, True)
        Column.add_attribute(crText, "text", 0)
        Column.add_attribute(crIcon, "stock-id", 1)
        crText.set_property("editable", True)
        crText.connect("edited", self.bookmarkTreeviewCell__Edited)
        self.bookmarkTreeview.append_column(Column)
        self.bookmarkTreeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.bookmarkTreeview.get_selection().connect("changed",
            self.bookmarkTreeviewSelectionChange)
        self.ConvertTVIterToModelIter = self.bookmarkTreeview.get_model().\
            convert_iter_to_child_iter;
        self.ConvertTVPathToModelPath = self.bookmarkTreeview.get_model().\
            convert_path_to_child_path;
        self.ConvertModelIterToTVIter = self.bookmarkTreeview.get_model().\
            convert_child_iter_to_iter;
        self.ConvertModelPathToTVPath = self.bookmarkTreeview.get_model().\
            convert_child_path_to_path;
        #end must be moved

        #sideBar-Button
        sideToolbar = self.uiManager.get_widget('/sideToolbar')
        gtke.setProperties(sideToolbar, toolbar_style=gtk.TOOLBAR_ICONS,
            tooltips=True, icon_size=gtk.ICON_SIZE_SMALL_TOOLBAR,
            icon_size_set=True)
        sideToolbarSlave = SlaveDelegate(toplevel=sideToolbar)
        self.attach_slave('sideToolbarPlaceholder', sideToolbarSlave)
        box = gtk.combo_box_new_text()
        for i in range(self.sideBarNotebook.get_n_pages()):
            box.append_text(self.sideBarNotebook.child_get_property(
                self.sideBarNotebook.get_nth_page(i), "tab-label"))
        box.set_active(self.sideBarNotebook.get_current_page())
        box.connect("changed", self.sidebarButtonChanged)
        ti = gtk.ToolItem()
        ti.add(box)
        ti.show_all()
        sideToolbar.insert(ti, 0)
        self.sideToolbarTogglebutton = ti
        self.sideToolbarGroups = list((self._getActionGroup('schemaGroup'),
            self._getActionGroup('historyGroup'),
            self._getActionGroup('bookmarksGroup')))
        self.sidebarButtonChanged(box)

        # Initialize the results status bar.
        self._statusInit()
        
        # queryState = None -> No query is made at this time, other values would
        # be an integer holding the thread number of the db-query-thread or a
        # tuple containing the id's of the function used by gobject
        self.queryState = None
        self.queryNum = 0
        # running total to id each query (used in case a query is aborted in 
        # favor of another one)
        

    #
    # RDF Model Management
    #

    _baseNs = {
        'rdf': commonns.rdf,
        'rdfs': commonns.rdfs,
        'relrdf': commonns.relrdf
     }

    def history_cell_needs_data(self, column, cell, model, iter):
        text = model.get_value(iter, 0)
        if not self.multilineHistory:
            text = text.replace("\r", "").replace("\n", " ")
        cell.set_property("text", text.strip("\n\r"))
        if model.get_path(iter)[0] == self.historyPos:
            cell.set_property("weight", 700)
        else:
            cell.set_property("weight", 400)
        cell.set_property("weight-set", True)
        if model.get_path(iter)[0] % 2 == 0:
            cell.set_property("background", "white")
        else:
            cell.set_property("background", "#AAAAAA")
    
    def openModel(self, modelBaseType, modelBaseArgs, modelType, modelArgs,
                  schModelBaseType=None, schModelBaseArgs=None,
                  schModelType=None, schModelArgs=None):
        # Open the main model.
        self.modelBase = relrdf.getModelBase(modelBaseType, **modelBaseArgs)
        self.model = self.modelBase.getModel(modelType, **modelArgs)

        # Create an appropriate URI shortener.
        self.shortener = nsshortener.NamespaceUriShortener(shortFmt='%s:%s',
                                                           longFmt='<%s>')
        self.shortener.addPrefix('rdf', commonns.rdf)
        self.shortener.addPrefix('rdfs', commonns.rdfs)
        self.shortener.addPrefix('relrdf', commonns.relrdf)

        # Add the namespaces from the model.
        self.shortener.addPrefixes(self.model.getPrefixes())

        if schModelBaseType is not None:
            # Open the schema model.
            self.schModelBase = relrdf.getModelBase(schModelBaseType,
                                               **schModelBaseArgs)
            self.schemaModel = self.schModelBase.getModel(schModelType,
                                                          **schModelArgs)

            # Add any additional namespaces from the schema model.
            self.shortener.addPrefixes(self.schemaModel.getPrefixes())
        else:
            # Use the same model for the schema.
            self.schModelBase = self.modelBase
            self.schemaModel = self.model

        # Create the schema pane.
        self.schemaBrowser.setSchema(schema.RdfSchema(self.schemaModel),
                                     self.shortener)

        self.showMessage("Model opened succesfully.")
        self.pageName = "%s (%s)" % (getObjectName(self.modelBase),
                                     getObjectName(self.model.mappingTransf))
        return self.pageName


    #
    # Query Execution and History
    #

    def runQuery(self, queryString):
        """Execute a query."""

        if self.model == None:
            return

        self._addToHistory(queryString)

        if THREADING:
            if self.queryState != None:
                md = gtk.MessageDialog(None, gtk.DIALOG_MODAL | 
                    gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING,
                    gtk.BUTTONS_YES_NO, "Current operation will be aborted!"
                    " Proceed?")
                Result = md.run()
                md.hide()
                if Result != gtk.RESPONSE_YES:
                    return
                elif isinstance(self.queryState, tuple):
                    # Results are processed via idle_add and timeout_add.
                    # These functions have to be aborted
                    for identifier in self.queryState:
                      gobject.source_remove(identifier)
            self.resultsStatus.push(self._baseStatusCtx, 
                _('Sending query to db...'))
            self.showMessage("Running query:\n\n\n" + queryString.strip("\n ")\
                + "\n\n\nPlease wait", True)
            self.queryState = self.queryNum
            gtke.newThreadAndIdleAdd(self.model.query, self.showResultsThreaded,
                self.queryThreadThrewException, ('SPARQL', queryString),
                (self.queryNum,), (self.queryNum,))
            self.queryNum += 1
        else:
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

    def queryThreadThrewException(self, exc, tb, queryNum):
        if self.queryState == queryNum:
            self.queryState = None
            self.resultsStatus.pop(self._baseStatusCtx)
            #self.showMessage(_("No results found"))
            self.hideResultCount()
            if isinstance(exc, relrdf.PositionError):
                self.queryEditor.markErrorExtents(exc.extents)
                self.showMessage("Syntax Error: %s" % exc.msg)
            else:
                try:
                    from traceback import format_exception
                    output = "An error occured while processing the query:\n\n"
                    for s in format_exception(type(exc), exc, tb):
                        output = output + s
                    self.showMessage(output)
                except:
                    self.showMessage("An error occured while processing the "
                        "query:\n\n" + str(exc) + "\n\nInstall the traceback "
                        "module to receive better error description")
                
    
    def backwardHistory(self):
        if self.historyPos >= len(self.history) - 1:
            return

        self.history[self.historyPos][0] = self.queryEditor.getQueryString()
        self.historyPos += 1
        self._updateHistoryState()

    def forwardHistory(self):
        if self.historyPos == 0:
            return
        
        self.history[self.historyPos][0] = self.queryEditor.getQueryString()
        self.historyPos -= 1
        self._updateHistoryState()
        
    def _addToHistory(self, queryString):
        # Do not store repeated queries.
        i = self.history.get_iter_first()
        while (i != None):
            if self.history.get_value(i, 0) == queryString:
                self.history.remove(i)
                break
            i = self.history.iter_next(i)

        while len(self.history) > self.maxHistorySize - 1:
            del self.history[self.maxHistorySize - 1]
        

        self.history.prepend((queryString,))
        self.historyPos = 0
        self._updateHistoryState()
        self.saveHistory(self.historyFileName)

    def _updateHistoryState(self):
        # Don't touch the editor if it isn't strictly
        # necessary. Changing the state may affect things like the
        # cursor position and undo history.
        if self.queryEditor.getQueryString() != \
               self.history[self.historyPos][0]:
            self.queryEditor.setQueryString(self.history[self.historyPos][0])

        self.forwardHistoryAction.set_sensitive(self.historyPos > 0)
        self.backwardHistoryAction.set_sensitive(self.historyPos < 
           len(self.history) - 1)
        self.historyTreeview.queue_draw()

    def saveHistory(self, filename):
        "saves the history list to the filename specified"
        f = open(filename, "w")
        f.writelines([escape(x[0])+"\n" for x in self.history])
        f.close()

    def loadHistory(self, filename):
        "reads the history list from the specified file"
        f = open(filename, "r")
        for line in f:
            if line != "":
                self.history.append((unescape(line),))
        f.close()

    def saveBookmarks__worker(self, model, path, iter, f):
        (name, text) = self.bookmarkStore.get(iter, 0, 2)
        if text == None:
            output = (str(" " * self.bookmarkStore.iter_depth(iter))) + "|" +\
                escape(name, {"|":"|"})
        else:
            output = (str(" " * self.bookmarkStore.iter_depth(iter))) + "|" +\
                escape(name, {"|":"|"}) + "|" + escape(text, {"|":"|"})
        f.write(output+"\n")
    
    def saveBookmarks(self, filename):
        f = open(filename+".new", "w")
        self.bookmarkStore.foreach(self.saveBookmarks__worker, f)
        f.close()
        
        
        cp = ConfigParser()
        iter = self.bookmarkStore.iter_children(
            self.bookmarkStore.get_iter_root())
        n = 0
        path = list(("root",))
        while (iter != False):
            # Depth-First over all nodes
            (name, text) = self.bookmarkStore.get(iter, 0, 2)
            sectionName = "Node" + str(n)
            cp.add_section(sectionName)
            cp.set(sectionName, "name", escape(name))
            if len(path) > 1:
                cp.set(sectionName, "contained", path[-1])
            if text != None:
                cp.set(sectionName, "contents", escape(text))
            if self.bookmarkStore.iter_has_child(iter):
                iter = self.bookmarkStore.iter_children(iter)
                path.append(sectionName)
            else:
                next = self.bookmarkStore.iter_next(iter)
                while next == None:
                    iter = self.bookmarkStore.iter_parent(iter)
                    if iter == None:
                        iter = False
                        next = False
                    else:
                        path.pop()
                        next = self.bookmarkStore.iter_next(iter)
                iter = next
            n+=1
        cp.write(file(filename, "w"))
        
    def setMultiline(self, onoff):
        if getattr(self, "setMultiline_working", False):
            return
        self.setMultiline_working = True
        try:
            self.historyMultilineMenuItem.set_active(onoff)
        except AttributeError:
            pass
        self.singlelineHistoryAction.set_active(not onoff)
        self.multilineHistoryAction.set_active(onoff)
        self.multilineHistory = onoff
        for col in self.historyTreeview.get_columns():
            col.queue_resize()
        self.setMultiline_working = False
      

    def loadBookmarks(self, filename):
        
        f = open(filename + ".new", "r")
        current_depth = 0
        parents = list()
        parent = self.bookmarkStore.get_iter_root()
        last = parent
        icons = {False: gtk.STOCK_DIRECTORY, True: gtk.STOCK_FILE}
        for line in f:
            Result = re.split(r'(?=(?:[^\\]|^)(?:\\\\))*\|', line)
            # Splits at non-escaped pipes "|"
            depth = len(Result[0])
            try:
                name = unescape(Result[1].rstrip())
                # trailing \n may be in string
            except IndexError:
                name = None
            try:
                text = unescape(Result[2].rstrip())
                # trailing \n may be in string
            except IndexError:
                text = None
            if name != None and depth > 0:
                if depth > current_depth:
                    current_depth += 1
                    parent = last
                while depth < current_depth:
                    parent = self.bookmarkStore.iter_parent(parent)
                    current_depth -= 1
                last = self.bookmarkStore.append(parent, 
                    (name, icons[text != None], text))
        f.close
        return
        
        cp = ConfigParser()
        cp.read(filename)
        folderList = dict()
        SectionsToDo = cp.sections()
        changed = True
        while len(SectionsToDo) > 0 and changed:
            SectionsToDo.sort()
            changed = False
            SkippedSections = list()
            for sectionName in SectionsToDo:
                name = unescape(cp.get(sectionName, "name"))
                if cp.has_option(sectionName, "contained"):
                    parent = folderList.get(cp.get(sectionName, "contained"),
                        None)
                else:
                    parent = self.bookmarkStore.get_iter_root()
                if parent != None:
                    if cp.has_option(sectionName, "contents"):
                        text = unescape(cp.get(sectionName, "contents"))
                        icon = gtk.STOCK_FILE
                    else:
                        text = None
                        icon = gtk.STOCK_DIRECTORY
                    folderList[sectionName] = self.bookmarkStore.append(parent,
                        (name, icon, text))
                    changed = True
                else:
                    SkippedSections.append(sectionName)
            SectionsToDo = SkippedSections


    #
    # Results Display
    #

    def showMessage(self, msg, waiting=False):
        """Show the message text in the window and display the specified
        message."""
        self.messageView.get_buffer().set_text(msg)
        self.resultsScrolled.hide()
        self.messageVBox.show()
        self.hideResultCount()
        for winType in (gtk.TEXT_WINDOW_WIDGET, gtk.TEXT_WINDOW_TEXT):
            win = self.messageView.get_window(winType)
            if win != None:
                if waiting:
                    win.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
                else:
                    win.set_cursor(None)

    def nodeToStr(self, node):
        if node is None:
            return ''
        elif isinstance(node, uri.Uri):
            return self.shortener.shortenUri(node)
        elif isinstance(node, literal.Literal):
            return '"%s"' % str(node.value)
        else:
            return "???"

    def showResultsThreaded(self, results, threadID):
        if threadID != self.queryState:
            # In this case the query has been aborted while querying the db.
            # Therefore the results are not needed
            return
        
        if results.resultType() == relrdf.RESULTS_MODIF:
            # Commit the changes.
            self.model.commit()

            self.resultsStatus.pop(self._baseStatusCtx)
            self.showMessage(_("Model modification operation successful: "
                               "%d statements affected") %
                             results.affectedRows)
            self.hideResultCount()
            self.queryState = None
            return

        # Determine the column names.
        if results.resultType() == relrdf.RESULTS_COLUMNS:
            columnNames = results.columnNames
        elif results.resultType() == relrdf.RESULTS_STMTS:
            columnNames = (_('subject'), _('predicate'), _('object'))
        else:
            assert False, "Unknown result type"

        # Create the list store. All columns contain strings.
        self.resultLS = gtk.ListStore(*([str] * len(columnNames)))

        if len(results) == 0:
            self.resultsStatus.pop(self._baseStatusCtx)
            self.showMessage(_("No results found"))
            self.hideResultCount()
            self.queryState = None
            return

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
            col = gtk.TreeViewColumn(name.replace('_', '__'))
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


        # Move the query results to the list store.
        generator = self._showResultsThreaded__insertresults(results)
        id1 = gobject.idle_add(generator.next)
        # _showResultsThreaded__insertresults is a generator function and
        # passing its next method to gobject.idle_add causes gtk to call the
        # generator whenever gtk is idle until the generator yields false.
        # See PyGTK-FAQ 20.9
        id2 = gobject.timeout_add(100, generator.next)
        self.queryState = (id1, id2)
        # Since this is running in the main thread there is no possibility that
        # queryState changed in the course of this method
        
    def _showResultsThreaded__insertresults(self, results):
        t = time.clock() + 1.5
        i = 0
        for result in results:
            self.resultLS.append([self.nodeToStr(node) for node in result])
            i += 1
            if time.clock() > t:
                t = time.clock() + 1
                self.resultsStatus.set_fraction(float(i) / float(len(results)))
            yield True

        # Show the results view.
        self.messageVBox.hide()

        # Set the new model.
        self.resultsView.set_model(self.resultLS)

        self.resultsScrolled.show()

        # Display the result count.
        self.resultsStatus.pop(self._baseStatusCtx)
        self.showResultCount(len(results))
        self.queryState = None # query has ended
        while 1:
            yield False
    

    def showResults(self, results):
        """Display the query results object as table."""
        if results.resultType() == relrdf.RESULTS_MODIF:
            # Commit the changes.
            self.model.commit()

            self.showMessage(_("Model modification operation succesful: "
                               "%d statements affected") %
                             results.affectedRows)
            self.hideResultCount()
            return

        # Determine the column names.
        if results.resultType() == relrdf.RESULTS_COLUMNS:
            columnNames = results.columnNames
        elif results.resultType() == relrdf.RESULTS_STMTS:
            columnNames = (_('subject'), _('predicate'), _('object'))
        else:
            assert False, "Unknown result type"

        # Create a list store for the results:

        # Create the list store. All columns contain strings.
        self.resultLS = gtk.ListStore(*([str] * len(columnNames)))

        if len(results) == 0:
            self.showMessage(_("No results"))
            self.hideResultCount()
            return

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
            col = gtk.TreeViewColumn(name.replace('_', '__'))
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


        # Move the query results to the list store.
        for result in results:
            self.resultLS.append([self.nodeToStr(node) for node in result])

        # Show the results view.
        self.messageVBox.hide()

        # Set the new model.
        self.resultsView.set_model(self.resultLS)

        self.resultsScrolled.show()

        # Display the result count.
        self.showResultCount(len(results))
        
        return False # if called by idle_add in a threaded environment

    #
    # Results Status Bar
    #

    def _statusInit(self):
        self.resultsStatus = gtke.Statusbar()
        self.lowerPane.pack_start(self.resultsStatus, False, True)
        self.resultsStatus.show()
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

    def on_mainPaned__realize(self, widget, *args):
        # Give the left pane a reazonable size.
        self.mainPaned.set_position(int(self.mainPaned.\
                                        get_property('max-position') * 0.3))

    def on_executeQueryAction__activate(self, widget, *args):
        self.runQuery(self.queryEditor.getQueryString())

    def on_backwardHistoryAction__activate(self, widget, *args):
        self.backwardHistory()

    def on_forwardHistoryAction__activate(self, widget, *args):
        self.forwardHistory()

    def on_multilineHistoryAction__toggled(self, action):
        self.setMultiline(True)
    
    def on_singlelineHistoryAction__toggled(self, action):
        self.setMultiline(False)
    
    def on_deleteHistoryAction__activate(self, widget, *args):
        dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL |
            gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, 
            gtk.BUTTONS_YES_NO, "Delete selected element(s)?")
        if dialog.run() == gtk.RESPONSE_YES:
            model, paths = self.historyTreeview.get_selection().\
                get_selected_rows()
            for path in paths:
                model.remove(model.get_iter(path))
            self.saveHistory(self.historyFileName)
        dialog.hide()
    
    def on_addBookmarkAction__activate(self, widget, *args):
        self.on_newBookmarkAction__activate(widget, *args)
    
    def on_newBookmarkAction__activate(self, widget, *args):
        paths = self.bookmarkTreeview.get_selection().get_selected_rows()[1]
        if len(paths) > 0:
            parent = self.bookmarkStore.get_iter(self.ConvertTVPathToModelPath(
                paths[0]))
            if self.bookmarkStore.get_value(parent, 2) != None:
                # parent is no folder
                parent = self.bookmarkStore.iter_parent(parent)
        else:
            parent = None
        (name, parent) = runBookmarkDialog("", self.bookmarkStore, parent,
            title="New Bookmark")
        if name != None:
            self.bookmarkStore.append(parent, (name, gtk.STOCK_FILE, self.\
                queryEditor.getQueryString()))
            self.saveBookmarks(self.bookmarkFileName)
    
    def on_newFolderAction__activate(self, widget, *args):
        paths = self.bookmarkTreeview.get_selection().get_selected_rows()[1]
        if len(paths) > 0:
            parent = self.bookmarkStore.get_iter(self.ConvertTVPathToModelPath(
                paths[0]))
            if self.bookmarkStore.get_value(parent, 2) != None:
                # parent is no folder
                parent = self.bookmarkStore.iter_parent(parent)
        else:
            parent = None
        (name, parent) = runBookmarkDialog("", self.bookmarkStore, parent,
            title="New Bookmark")
        if name != None:
            self.bookmarkStore.append(parent, (name, gtk.STOCK_DIRECTORY, None))
            self.saveBookmarks(self.bookmarkFileName)
    
    def on_deleteBookmarkAction__activate(self, widget, *args):
        dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL |
            gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_YES_NO, "Delete selected element(s)?")
        if dialog.run() == gtk.RESPONSE_YES:
            for iterator in map(lambda path: self.bookmarkTreeview.get_model().\
                get_model().get_iter(self.ConvertTVPathToModelPath(path)),
                self.bookmarkTreeview.get_selection().get_selected_rows()[1]):
                  self.bookmarkStore.remove(iterator)
            self.saveBookmarks(self.bookmarkFileName)
        dialog.destroy()
        
    def on_showHistoryAction__activate(self, widget, *args):
        "Creates and shows a popup menu containing the history-list"
        popup = gtk.Menu()
        i = 0
        group = None
        for i in range(self.maxHistoryMenuSize):
            item = gtk.RadioMenuItem(group, textwrap.fill(re.sub(r"\s+", " ",
                                     self.history[i][0]), 80))
            if group == None: group = item
            item.set_active(i == self.historyPos)
            item.connect("activate", self.popupMenu__activate, i);
            i += 1
            item.show()
            popup.append(item)
            
        if len(popup) > 0:
            popup.popup(None, None, None, 1, 0)
   
    def popupMenu__activate(self, item, history_num):
        """Called by a click on a item of the history list. Shows the 
        specified item in the Query Editor"""
        self.history[self.historyPos][0] = self.queryEditor.getQueryString()
        self.historyPos = history_num
        self._updateHistoryState()
        
    def on_resultsView__drag_data_get(self, widget, context, selection,
                                      targetType, eventTime):
        (path, col) = self.resultsView.get_cursor()
        tItr = self.resultLS.get_iter(path)
        entries = self.resultLS.get(tItr, *range(self. \
                                                 resultLS.get_n_columns()))
        selection.set(selection.target, 8, string.join(entries, ' '))

    def on_HistoryTreeview__row_activated(self, treeview, path, viewColumn):
        self.historyPos = path[0]
        self._updateHistoryState()
    
    def on_BookmarksTreeview__row_activated(self, treeview, path, viewColumn):
        self.queryEditor.setQueryString(self.bookmarkStore.get_value(self.\
            bookmarkStore.get_iter(self.ConvertTVPathToModelPath(path)), 2))

    # JB 12.02.2007:
    # ! This method is connected by a call to connect, not by kiwi
    def queryEditor__key_press_event(self, widget, event):
        '''handles the "key_press_event" signal to search for Ctrl+Enter.
        If found runQuery is called'''
        if ((event.keyval == gtk.keysyms.Return) and (event.get_state() & 
            gtk.gdk.CONTROL_MASK)):
                self.runQuery(self.queryEditor.getQueryString())
                return True
        else:
                return False
    
    def bookmarkTreeviewSelectionChange(self, selection):
        (model, rows) = selection.get_selected_rows()
        if len(rows) == 0:
            self.uiManager.get_action('/bookmarksToolbar/newBookmarkAction').\
                set_sensitive(True)
            self.uiManager.get_action('/bookmarksToolbar/newFolderAction').\
                set_sensitive(True)
            self.uiManager.get_action('/bookmarksToolbar/deleteBookmarkAction')\
                .set_sensitive(False)
        elif len(rows) == 1:
            self.uiManager.get_action('/bookmarksToolbar/newBookmarkAction')\
                .set_sensitive(True)
            self.uiManager.get_action('/bookmarksToolbar/newFolderAction')\
                .set_sensitive(True)
            self.uiManager.get_action('/bookmarksToolbar/deleteBookmarkAction')\
                .set_sensitive(True)
        else:
            self.uiManager.get_action('/bookmarksToolbar/newBookmarkAction')\
                .set_sensitive(False)
            self.uiManager.get_action('/bookmarksToolbar/newFolderAction')\
                .set_sensitive(False)
            self.uiManager.get_action('/bookmarksToolbar/deleteBookmarkAction')\
                .set_sensitive(True)

    def bookmarkTreeviewCell__Edited(self, cellrenderer, path, new_text):
        self.bookmarkStore.set(self.bookmarkStore.get_iter(self.\
            ConvertTVPathToModelPath(path)), 0, new_text)
        self.saveBookmarks(self.bookmarkFileName)

    def sidebarButtonChanged(self, combobox):
        page_num = combobox.get_active()
        if page_num < 0:
            combobox.set_active(self.sideBarNotebook.get_current_page())
            return
        self.sideToolbarTogglebutton.hide()
        self.sideBarNotebook.set_current_page(page_num)
        for i in range(len(self.sideToolbarGroups)):
            self.sideToolbarGroups[i].set_visible(page_num == i)
        self.sideToolbarTogglebutton.show()

    def close(self):
        # Close the models and model bases.
        if self.schemaModel is not self.model:
            self.schemaModel.close()
            self.schModelBase.close()
        self.model.close()
        self.modelBase.close()


class MainWindow(UiManagerDelegate):
    """Main browser window."""

    mainGroup__actions = [('fileAction', None, _('_File'), None, None),
                          ('openAction', gtk.STOCK_OPEN, None, None, None),
                          ('quitAction', gtk.STOCK_QUIT, None, None, None),
                          ('viewAction', None, _('_View'), None, None),
                          ('historyAction', None, _('History'), None, None)]

    mainGroup__toggleActions = [('viewSideBarAction',
                                 None,
                                 _('_Side Bar'),
                                 'F9',
                                 None,
                                 None,
                                 True),
                                ('historyOneLineAction',
                                None,
                                _('Multiline History'),
                                None,
                                None,
                                None,
                                True)]

    uiDefinition = '''<ui>
    <menubar name="menuBar">
      <menu action="fileAction">
        <menuitem action="openAction"/>
        <separator/>
        <menuitem action="quitAction"/>
      </menu>
      <menu action="viewAction">
        <menuitem action="viewSideBarAction"/>
        <separator/>
        <menu action="historyAction">
          <menuitem action="historyOneLineAction"/>
        </menu>
      </menu>
    </menubar>
    </ui>'''

    def __init__(self):
        UiManagerDelegate.__init__(self,
                                   gladefile='browser.glade',
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

        menu = self.uiManager.get_widget('/menuBar')
        menuSlave = SlaveDelegate(toplevel=menu)
        self.attach_slave('menuBar', menuSlave)

        self.notebook = self.get_widget("notebook1")
        self.notebook.popup_enable()
        self.notebook.set_group_id(0)

        self.appName = self.mainWindow.get_title()

    def openModel(self, modelBaseType, modelBaseArgs, modelType, modelArgs,
                  schModelBaseType=None, schModelBaseArgs=None,
                  schModelType=None, schModelArgs=None):
        new_page = NotebookPage()
        new_widget = new_page.get_toplevel()
        new_widget.delegate = new_page
        page_name = new_page.openModel(modelBaseType, modelBaseArgs, modelType, 
            modelArgs, schModelBaseType=None, schModelBaseArgs=None,
            schModelType=None, schModelArgs=None)
        vbox = gtk.HBox()
        LabelBox = gtke.EventBox(gtk.Label(page_name))
        LabelBox.connect("event", self.ShowTabMenu, new_widget)
        vbox.pack_start(LabelBox)
        CloseBox = gtke.EventBox(gtk.image_new_from_stock(gtk.STOCK_CLOSE,
            gtk.ICON_SIZE_MENU))
        CloseBox.connect("button-press-event", self.CloseTab, new_widget)
        vbox.pack_start(CloseBox)
        vbox.show_all()
        
        pane_pos = new_page.get_widget('mainPaned').get_position()
        pageNum = self.notebook.append_page(new_widget, vbox)
        gtke.setChildProperties(self.notebook, new_widget, menu_label=page_name,
            reorderable=True, detachable=True)
        self.notebook.set_current_page(pageNum)
        new_page.get_widget('mainPaned').set_position(pane_pos)
        self.mainWindow.set_title(page_name + " - " + self.appName)
        new_page.historyMultilineMenuItem = self.uiManager.get_widget(
            "/menuBar/viewAction/historyAction/historyOneLineAction")

    def CloseTab(self, widget, event, tab):
        self.notebook.remove_page(self.notebook.child_get_property(tab,
            "position"))
        delegate = tab.delegate
        delegate.close()
        tab.delegate = None
        tab.destroy()
    
    def ShowTabMenu(self, widget, event, tab):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            Menu = gtk.Menu()
            for i in range(self.notebook.get_n_pages()):
                item = gtk.MenuItem(self.notebook.child_get_property(self.\
                    notebook.get_nth_page(i), "menu-label"))
                gtke.staticConnect(item, "activate", self.\
                    notebook.set_current_page, i)
                Menu.append(item)
            Menu.append(gtk.SeparatorMenuItem())
            item = gtk.ImageMenuItem(stock_id=gtk.STOCK_CLOSE)
            item.connect("activate", self.CloseTab, None, self.notebook.\
                get_nth_page(self.notebook.get_current_page()))
            Menu.append(item)
            Menu.show_all()
            Menu.popup(None, None, None, event.button, event.time)
            return True
    
    def finalize(self):
        # Run the close method on the tabs.
        for i in range(self.notebook.get_n_pages()):
            self.notebook.get_nth_page(i).delegate.close()

        gtk.main_quit()

    def on_mainWindow__delete_event(self, widget, *args):
        self.finalize()
        return False

    def on_quitAction__activate(self, widget, *args):
        self.finalize()

    def on_openAction__activate(self, widget, *args):
        Result = promptModel()
        if Result != False:
            self.openModel(*Result)

    def on_viewSideBarAction__toggled(self, action):
       if action.get_active():
           self.notebook.get_nth_page(self.notebook.get_current_page()).\
              delegate.sidePaneVBox.show()
       else:
           self.notebook.get_nth_page(self.notebook.get_current_page()).\
              delegate.sidePaneVBox.hide()
            
    def on_historyOneLineAction__toggled(self, action):
        activePage = self.notebook.get_nth_page(self.notebook.\
            get_current_page())
        activePage.delegate.setMultiline(action.get_active())
    
    def on_notebook1__switch_page(self, notebook, page, page_num):
        # Hint: page is not usable as it is GPointer
        activePage = notebook.get_nth_page(page_num)
        self.uiManager.get_action('/menuBar/viewAction/viewSideBarAction').\
            set_active(activePage.delegate.sidePaneVBox.get_property("visible"))
        self.uiManager.get_action('/menuBar/viewAction/historyAction/'
            'historyOneLineAction').set_active(activePage.\
            delegate.multilineHistory)
        pgName = self.notebook.child_get_property(activePage, "menu-label")
        if isinstance(pgName, basestring):
            self.mainWindow.set_title(pgName + " - " + self.appName)
        else:
            self.mainWindow.set_title(self.appName)
    
    def on_notebook1__page_added(self, notebook, child, page_num):
        notebook.set_show_tabs(notebook.get_n_pages() > 1)
        
    def on_notebook1__page_removed(self, notebook, child, page_num):
        notebook.set_show_tabs(notebook.get_n_pages() > 1)

def main():
    from relrdf.error import InstantiationError
    from relrdf.factory import parseCmdLineArgs

    if len(sys.argv) < 2:
        main_window = MainWindow()
        initparams = promptModel()
        main_window.openModel(*initparams)
    #    print >> sys.stderr, \
    #          _("usage: browser :<model base type> [<model base params] "
    #            ":<model type> [<model params>]")
    #    sys.exit(1)
    else:
        argv = list(sys.argv[1:])
        try:
            baseType, baseArgs = parseCmdLineArgs(argv, _('model base'))
            modelType, modelArgs = parseCmdLineArgs(argv, _('model'))
        
            main_window = MainWindow()
        
            if len(argv) > 0:
                schBaseType, schBaseArgs = \
                    parseCmdLineArgs(argv, _('schema model base'))
                schModelType, schModelArgs = \
                    parseCmdLineArgs(argv, _('schema model'))
        
                main_window.openModel(baseType, baseArgs, modelType, modelArgs,
                                      schBaseType, schBaseArgs,
                                      schModelType, schModelArgs)
            else:
                main_window.openModel(baseType, baseArgs, modelType, modelArgs)
        
        except InstantiationError, e:
            
            print >> sys.stderr, _("Error: %s") % e
            sys.exit(1)

    main_window.show()

    gtk.main()


if __name__ == "__main__":
    main()
