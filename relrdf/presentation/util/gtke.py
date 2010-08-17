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
import thread
import gobject
import sys

def setProperties(Widget, Properties = {}, **kwargs):
    "set Properties of widget specified by the dict in Properties"
    for property in Properties:
        Widget.set_property(property, Properties[property])
    for property in kwargs:
        Widget.set_property(property.replace("_", "-"), kwargs[property])

def setChildProperties(Parent, Child, Properties = {}, **kwargs):
    """set Child-Properties of widget's child Child specified
    by the dict in Properties"""
    for property in Properties:
        Parent.child_set_property(Child, property, Properties[property])
    for property in kwargs:
        Parent.child_set_property(Child, property.replace("_", "-"),
            kwargs[property])

def staticConnect(widget, signal, function, *parameter):
    "Connects signal of widget to the static call to function(*parameter)"
    return widget.connect(signal, __staticConnectCallback, function, parameter)
    
def __staticConnectCallback(*args):
    "Helper Function for staticConnect"
    return args[-2](*args[-1])

def queryString(label="Enter text", title=None, default=""):
    "Displays a dialog box and queries the user to enter a string"
    if getattr(queryString, "dialog", None) == None:
        queryString.dialog = gtk.Dialog(None, None, gtk.DIALOG_MODAL | 
            gtk.DIALOG_DESTROY_WITH_PARENT, (gtk.STOCK_CANCEL,
            gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
        box = gtk.VBox()
        queryString.label = gtk.Label()
        box.pack_start(queryString.label, False)
        queryString.entry = gtk.Entry()
        staticConnect(queryString.entry, "activate", 
            queryString.dialog.response, gtk.RESPONSE_OK)
        box.pack_start(queryString.entry, False)
        box.show_all()
        queryString.dialog.vbox.pack_start(box)
        queryString.dialog.set_default_response(gtk.RESPONSE_OK)
    queryString.label.set_text(label)
    queryString.entry.set_text(default)
    queryString.dialog.set_title(title)
    Result = queryString.dialog.run()
    queryString.dialog.hide()
    if Result == gtk.RESPONSE_OK:
        return queryString.entry.get_text()
    else:
        return False

def EventBox(Child):
    "Creates new gtk.EventBox with Child as child"
    eb = gtk.EventBox()
    eb.add(Child)
    return eb

def createStringListView(title = "", items = None, attributeDefinition = None,
                  userData = True, treeview = None, treeviewProperties = None):
    '''Creates a Gtk TreeView with a ListStore in which a single column is 
       created.
    
    Arguments:
      title: The title of the list column (default is "") or a list of titles
      items: A list of strings (or a list of a list of strings), that are read 
      into the ListStore
      userData: indicates if an extra col to store userData should be create 
                (default: True)
      treeview: The treeview where to add the data (if None or omitted, a 
                new one is created)
      treeviewProperties: A dictionary that contains the names of properties to
                          set on the TreeView. May contain a key 
                          "TreeViewColumn" which has a dict as value. This will
                          be used to set the properties of all Columns. Same
                          is for "CellRenderer"
      
    Returns:
      the created TreeView'''
    
    # e.g.("col 0", (text, str), (color, gtk.color))
    
    if items == None:
        items = list()
    cols = list()
    if isinstance(title, basestring):
        if attributeDefinition == None:
            attributeDefinition = ((title, ("text", str)),)
    else:
        if attributeDefinition == None:
            attributeDefinition = list()
            for x in title:
                attributeDefinition.append((x, ("text", str)))
    for visibleCol in attributeDefinition:
        cols.extend(map(lambda x: x[1], visibleCol[1:]))
    if userData:
        cols.append(object)
    if treeviewProperties == None:
        treeviewProperties = dict()
    store = gtk.ListStore(*cols)
    colcount = len(cols)
    for item in items:
        if isinstance(item, basestring):
            data = [item]
        else:
            data = list(item)
        if len(data) < colcount:
            data.extend([None] * (colcount - len(data)))
        store.append(data[:colcount])
    if treeview == None:
        treeview = TreeView()
    tvcol_props = dict()
    tvcr_props = dict()
    for (key, value) in treeviewProperties.items():
        if key == "TreeViewColumn":
            tvcol_props = value
        elif key == "CellRenderer":
            tvcr_props = value
        else:
            treeview.set_property(key, value)
    offset = 0
    for visibleCol in attributeDefinition:
        cr = gtk.CellRendererText()
        for (key, value) in tvcr_props.items():
            cr.set_property(key, value)
        attr = dict(zip(map(lambda x: x[0], visibleCol[1:]), range(offset,
            offset + len(visibleCol) - 1)))
        offset += len(visibleCol)
        tc = gtk.TreeViewColumn(visibleCol[0], cr, **attr)
        for (key, value) in tvcol_props.items():
            tc.set_property(key, value)
        treeview.append_column(tc)
    treeview.set_model(store)
    return treeview

def TreeView_getSelectedValue(TreeView):
    """Returns the value of the first column of the selected row(s).
    
    The return type is a list if the selection mode is SELECTION_MULTIPLE
    (even if only one row is selected) and a single value otherwise"""
    (model, rows) = TreeView.get_selection().get_selected_rows()
    if len(rows) == 0:
        return None
    elif TreeView.get_selection().get_mode() == gtk.SELECTION_MULTIPLE:
        return map(lambda row: model.get_value(model.get_iter(row), 0), rows)
    else:
        return model.get_value(model.get_iter(rows[0]), 0)

def TreeView_getSelectedUserData(TreeView):
    """Returns the value of the last column of the selected row(s).
    
    The return type is a list if the selection mode is SELECTION_MULTIPLE 
    (even if only one row is selected) and a single value otherwise"""
    (model, rows) = TreeView.get_selection().get_selected_rows()
    if len(rows) == 0:
        return None
    col = model.get_n_columns() - 1
    if TreeView.get_selection().get_mode() == gtk.SELECTION_MULTIPLE:
        return map(lambda row: model.get_value(model.get_iter(row), col), rows)
    else:
        return model.get_value(model.get_iter(rows[0]), col)

def TreeView_getValueAt(TreeView, x, y):
    "Returns the value of the first colums of the row at given coordinates"
    data = TreeView.get_path_at_pos(x, y)
    if data == None: return None
    model = TreeView.get_model()
    return model.get_value(model.get_iter(data[0]), 0)

def TreeView_getUserDataAt(TreeView, x, y):
    "Returns the value of the first colums of the row at given coordinates"
    data = TreeView.get_path_at_pos(x, y)
    if data == None: return None
    model = TreeView.get_model()
    return model.get_value(model.get_iter(data[0]), model.get_n_columns() - 1)

def TreeView_selectByValue(TreeView, Value):
    "Selects each row if it contains the given Value"
    model = TreeView.get_model()
    n_cols = model.get_n_columns()
    selection = TreeView.get_selection()
    model.foreach(lambda model, path, iter: (Value in model.get(iter, *[i for i
        in range(n_cols)])) and selection.select_iter(iter))
    

def TreeView_selectByUserData(TreeView, data):
    "Selects each row if it contains the given user data"
    model = TreeView.get_model()
    col = model.get_n_columns() - 1
    selection = TreeView.get_selection()
    model.foreach(lambda model, path, iter: (data in model.get(iter, col)) and 
        selection.select_iter(iter))
        
class TreeView(gtk.TreeView):
    def getSelectedValue(self):
        return TreeView_getSelectedValue(self)
    def getSelectedUserData(self):
        return TreeView_getSelectedUserData(self)
    def getValueAt(self, x, y):
        return TreeView_getValueAt(self, x, y)
    def getUserDataAt(self, x, y):
        return TreeView_getUserDataAt(self, x, y)
    def selectByValue(self, Value):
        return TreeView_selectByValue(self, Value)
    def selectByUserData(self, data):
        return TreeView_selectByUserData(self, data)

class AssistantPage(object):
    """Abstract base class to control the contents and page-flow of an 
    gtk.Assistant
    
    This class must be inherited together with a descendant of gtk.Widget in 
    order to work correctly. This class appends itsself to its gtk.Assistant,
    sets the title, pageType and the images. 
    """
    
    writethrough = ("complete",
                    "header_image",
                    "page_type",
                    "sidebar_image",
                    "title")
    """mapped attributes of the page
    
    Access to these attributes is mapped to properties of the assistant.
    Underscores (_) are transformed to minus (-) before accessing the property
    """
    
    def __init__(self, parent):
        self.assistant = parent
        self.pagenum = self.assistant.append_page(self)
        for property in self.writethrough:
            if hasattr(self, property):
                self.assistant.child_set_property(self, property, getattr(self,
                    property))
        self.prepare_handler_id = None
        self.apply_handler_id = None
        self.auto_show_all = True
        self.show()

    def __getattr__(self, name):
        if name in self.writethrough:
            if getattr(self, "assistant", None) != None:
                return self.assistant.child_get_property(self, name.replace
                    ("_", "-"))
            else:
                return None
        else:
            raise AttributeError, "'" + str(type(self)) +\
                "' object has no attribute '" + name + "'"
            
    def __setattr__(self, name, value):
        if name in self.writethrough:
            if getattr(self, "assistant", None) != None:
                try:
                    self.assistant.child_set_property(self, name.replace(
                        "_", "-"), value)
                except Exception, detail:
                    raise AttributeError, "setting '" + name.replace("_", "-")\
                        + "' to '" + str(value) + "' raised following error: "\
                        + str(detail)
            else:
                raise AttributeError, "'" + type(self) +\
                "' object need assistant set in order to set '" + name + "'"
        else:
            super(AssistantPage, self).__setattr__(name, value)
    
    def createPage(self):
        """Create the page to be displayed
        
        The page should be created and shown, ready to be displayed"""
        pass

    def setPageActive(self):
        #self.assistant.set_forward_page_func(self.ForwardPageFunc)
        if self.prepare_handler_id != None:
            self.assistant.disconnect(self.prepare_handler_id)
        self.prepare_handler_id = self.assistant.connect("prepare",
            self.prepare_func)
        if self.apply_handler_id != None:
            self.assistant.disconnect(self.apply_handler_id)
        self.apply_handler_id = self.assistant.connect("apply", self.apply_func)
        if hasattr(self, "actionButtons"):
            page_buttons = self.actionButtons
            if callable(page_buttons):
                page_buttons = page_buttons()
            for button in page_buttons:
                self.assistant.add_action_widget(button)
                button.show()
        
    def setPageInactive(self):
        if self.prepare_handler_id != None:
            self.assistant.disconnect(self.prepare_handler_id)
        self.prepare_handler_id = None
        if self.apply_handler_id != None:
            self.assistant.disconnect(self.apply_handler_id)
        self.apply_handler_id = None
        if hasattr(self, "actionButtons"):
            page_buttons = self.actionButtons
            if callable(page_buttons):
                page_buttons = page_buttons()
            for button in page_buttons:
                self.assistant.remove_action_widget(button)
                button.hide()

    def setPageSkip(self, toSkip=0):
        visible = self.pagenum + toSkip
        for i in range(self.pagenum + 1, self.assistant.get_n_pages()):
            self.assistant.get_nth_page(i).set_property("visible", i > visible)
    
    def prepare_func(self, assistant, page):
        if page == self:
            return
        self.pageFinished()
        self.setPageInactive()
        if isinstance(page, AssistantPage):
            page.preparePage()

    def apply_func(self, widget):
        self.pageFinished()
    
    def pageFinished(self):
        pass

    def preparePage(self):
        self.createPage()
        if self.auto_show_all:
            self.show_all()
        else:
            self.show()
        self.setPageActive()

class AssistantTable(gtk.Table, AssistantPage):
    def __init__(self, parent, rows=1, columns=1, homogeneous=False):
        gtk.Table.__init__(self, rows, columns, homogeneous)
        AssistantPage.__init__(self, parent)
    
class AssistantVBox(gtk.VBox, AssistantPage):
    def __init__(self, parent, homogeneous=False, spacing=0):
        gtk.VBox.__init__(self, homogeneous, spacing)
        AssistantPage.__init__(self, parent)

class AssistantHBox(gtk.HBox, AssistantPage):
    def __init__(self, parent, homogeneous=False, spacing=0):
        gtk.HBox.__init__(self, homogeneous, spacing)
        AssistantPage.__init__(self, parent)

class AssistantDialog(gtk.Assistant):
    def __init__(self):
        gtk.Assistant.__init__(self)
        self.running = False
        self.success = None
        self.connect("cancel", self.__DialogClose, False)
        self.connect("close", self.__DialogClose, True)
        
    def forward(self):
        Fwd = self.getActionButton(gtk.STOCK_GO_FORWARD)
        if Fwd.get_property("visible"):
            Fwd.activate()
        else:
            App = self.getActionButton(gtk.STOCK_APPLY)
            if App.get_property("visible"):
                App.activate()
            else:
                Cle = self.getActionButton(gtk.STOCK_CLOSE)
                if Cle.get_property("visible"):
                    Cle.activate()
                else:
                    self.emit("close") # fallback
    
    def run(self, parent=None, showall=False):
        self.set_modal(True)
        self.set_transient_for(parent)
        if showall:
            self.show_all()
        else:
            self.show()
        self.running = True
        gtk.main()
        return self.success

    def __DialogClose(self, assistant, success):
        self.success = success
        if self.running:
            self.running = False
            gtk.main_quit()
            
    def getActionButton(self, stock_id):
        """Hack to get access to the internal action buttons, may not work with
        future versions"""
        result = list()
        self.forall(self.__getActionButton, (gtk.stock_lookup(stock_id)[0], result))
        if len(result) > 0:
            return result[0]
        else:
            return None
            
    def __getActionButton(self, start, (stock_str, result)):
        """Hack to get access to the internal action buttons, 
        may not work with future versions"""
        if isinstance(start, gtk.Button):
            if start.get_use_stock() and start.get_property("label") ==\
                stock_str:
                    result.append(start)
        elif isinstance(start, gtk.Container):
            start.forall(self.__getActionButton, (stock_str, result))
        

def EntryWithCompletition(completion_entries, max = 0):
    """creates a gtk.Entry with a gtk.EntryCompletition and inserts the list 
    into the EntryCompletition"""
    entry = gtk.Entry(max)
    completion = gtk.EntryCompletion()
    model = gtk.ListStore(str)
    for e in completion_entries:
        model.append((e,))
    completion.set_model(model)
    completion.set_text_column(0)
    entry.set_completion(completion)
    return entry

class gThread(object):
    "Untested!"
    def __init__(self, runFunc = None, callbackFunc = None, 
                 exceptionFunc = None, useThreadingModule = False, 
                 name = None, group = None):
        object.__init__(self)
        self.useThreading = useThreadingModule
        self.runFunc = None
        self.runArgs = list()
        self.runKwargs = dict()
        if callable(runFunc):
            self.runFunc = runFunc
        elif runFunc != None:
            l = list(runFunc)
            self.runFunc = l[0]
            try:
                self.runArgs = l[1]
                self.runKwargs = l[2]
            except IndexError:
                pass
        self.callbackFunc = None
        self.callbackArgs = list()
        self.callbackKwargs = dict()
        if callable(callbackFunc):
            self.callbackFunc = callbackFunc
        elif callbackFunc != None:
            l = list(callbackFunc)
            self.callbackFunc = l[0]
            try:
                self.callbackArgs = l[1]
                self.callbackKwargs = l[2]
            except IndexError:
                pass
        self.exceptionFunc = None
        self.exceptionArgs = list()
        self.exceptionKwargs = dict()
        if callable(exceptionFunc):
            self.exceptionFunc = exceptionFunc
        elif exceptionFunc != None:
            l = list(exceptionFunc)
            self.exceptionFunc = l[0]
            try:
                self.exceptionArgs = l[1]
                self.exceptionKwargs = l[2]
            except IndexError:
                pass
        self.name = name
        self.group = group
        
    def setRunFunction(self, function = None, *args, **kwargs):
        self.runFunc = function
        self.runArgs = args
        self.runKwargs = kwargs
    
    def setCallbackFunction(self, function = None, *args, **kwargs):
        self.callbackFunc = function
        self.callbackArgs = args
        self.callbackKwargs = kwargs

    def setExceptionFunction(self, function = None, *args, **kwargs):
        self.exceptionFunc = function
        self.exceptionArgs = args
        self.exceptionKwargs = kwargs
        
    def useThreadingModule(self, mode=None):
        if mode != None:
            self.useThreading = mode
        return self.useThreading
        
    def __call__(self):
        assert(self.runFunc != None)
        if self.useThreading:
            self.ThreadObject = threading.Thread(group=self.group, target=\
                self._threadCode)
            self.ThreadObject.start()
        else:
            self.ThreadObject = thread.start_new_thread(self._threadCode)
        return ThreadObject
    
    def _threadCode(self):
        try:
            Result = self.runFunc(self.ThreadObject, *self.runArgs, 
                **self.runKwargs)
        except Exception, e:
            if self.exceptionFunc != None:
                gobject.idle_add(self.exceptionFunc, self.ThreadObject, e, 
                    sys.exc_info()[2], *self.exceptionArgs, 
                    **self.exceptionKwargs)
            else:
                sys.excepthook(*sys.exc_info()) # Print Exception to console
        else:
            gobject.idle_add(self.callbackFunc, self.ThreadObject, Result, 
                *self.callbackArgs, **self.callbackKwargs)

def newThreadAndIdleAdd(ThreadFunc, IdleAddFunc, ExceptFunc, ThreadArgs = (), 
                        IdleAddArgs = (), ExceptArgs = (), ThreadKwargs = {}):
    """creates a new thread which executes ThreadFunc and when finished calls 
    gobject.idle_add
    
    The function ThreadFunc is called in the context of a new thread. The 
    function is given the arguments from the ThreadArgs list and the keyword-
    arguments of the ThreadKwargs dictionary. After the (succesful) return of
    the ThreadFunc the function IdleAddFunc is added to gobjecs idle list by
    calling gobject.idle_add. IdleAddFunc's parameters will be (in that order):
    self (only if called as a bound method), Result of ThreadFunc and the 
    parameters from IdleAddArgs.
    
    Hint: as IdleAddFunc is called by gtk as any other idle_add function it 
      should return False in order to be called only once"""
    return thread.start_new_thread(_newThreadAndIdleAdd__RunFunc, 
        (ThreadFunc, ThreadArgs, ThreadKwargs, IdleAddFunc, IdleAddArgs,
        ExceptFunc, ExceptArgs))

def _newThreadAndIdleAdd__RunFunc(ThreadFunc, ThreadArgs, ThreadKwargs,
                            IdleAddFunc, IdleAddArgs, ExceptFunc, ExceptArgs):
    try:
        Result = ThreadFunc(*ThreadArgs, **ThreadKwargs)
    except Exception, e:
        gobject.idle_add(ExceptFunc, e, sys.exc_info()[2], *ExceptArgs)
    else:
        gobject.idle_add(IdleAddFunc, Result, *IdleAddArgs)

class Statusbar(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self)
        gtk.HBox.__setattr__(self, "Statusbar", gtk.Statusbar())
        gtk.HBox.__setattr__(self, "Progressbar", gtk.ProgressBar())
        self.pack_start(self.Statusbar)
        self.Statusbar.show()
        self.currentlyShowing = self.Statusbar
        
    def showStatusbar(self):
        if self.currentlyShowing != self.Statusbar:
            self.Progressbar.hide()
            self.remove(self.Progressbar)
            self.pack_start(self.Statusbar)
            self.Statusbar.show()
            self.currentlyShowing = self.Statusbar
            
    def showProgressbar(self):
        if self.currentlyShowing != self.Progressbar:
            self.Statusbar.hide()
            self.remove(self.Statusbar)
            self.pack_start(self.Progressbar)
            self.Progressbar.show()
            self.currentlyShowing = self.Progressbar
    
    def __getattr__(self, name):
        if hasattr(self.Statusbar, name):
            self.showStatusbar()
            return getattr(self.Statusbar, name)
        elif hasattr(self.Progressbar, name):
            self.showProgressbar()
            return getattr(self.Progressbar, name)
        else:
            raise AttributeError()
            
    def __setattr__(self, name, value):
        if hasattr(self, name):
            gtk.HBox.__setattr__(self, name, value)
        elif hasattr(self.Statusbar, name):
            self.Statusbar.__setattr__(name, value)
            self.showStatusbar()
        elif hasattr(self.Progressbar, name):
            self.Progressbar.__setattr__(name, value)
            self.showProgressbar()
        else:
            gtk.HBox.__setattr__(self, name, value)
