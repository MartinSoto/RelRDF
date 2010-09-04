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

#TODO:
# - predefs auf aktuelle Parameter pruefen
# - Fehler farbig anzeigen?
# - 2way and 3way - Compararision Mapper: 
#   Check if two or three versions are the same?
# - set standard size for dialog
# - db-description in xml?


# Browser:
# history links anzeigen (verstecken koennen)
# Tabs zulassen
# Queries speichern
# History pro Mapping und Datenbank (eigentlich Schema) speichern

import gtk
import gtk.glade
import pango

import gtke
from Config import CaseSensitiveConfigParser, getCFGFilename
from relrdf.centralfactory import getModelBases

def getObjectName(obj):
    if hasattr(obj, "name"):
        if callable(obj.name):
            return str(obj.name())
        else:
            return str(obj.name)
    else:
      return str(obj)

def getDBModels(db, parameter):
    if hasattr(db, "getModelInfo") and callable(db.getModelInfo):
        return dict(db.getModelInfo(**parameter))
    else:
        return dict()

def getParameterInfo(db):
    if hasattr(db, "parameterInfo"):
        p = db.parameterInfo
        if callable(p):
            p = p()
        return list(p)
        # list because p could be an iterator and we want to return a list
    else:
        return list()

class modelConfiguration(object):
    __slots__ = ("name",
                 "modelbase",
                 "modelbaseParameter",
                 "models",
                 "std_model")
    def __init__(self, name, modelbase = None, modelbaseParameter = None, 
                models = None, std_model = None):
        self.name = name
        self.modelbase = modelbase
        self.modelbaseParameter = modelbaseParameter
        if self.modelbaseParameter == None:
            self.modelbaseParameter = dict()
        self.models = models
        if self.models == None:
            self.models = dict()
        self.std_model = std_model
        
    def getModelbaseClass(self, databases):
        Resultlist = filter(lambda db: getObjectName(db) == self.modelbase,
            databases)
        if len(Resultlist) == 0:
            return None
        else:
            return Resultlist[0]
        
#Zum speichern nicht namen als sektionsnamen verwenden, sonder numerieren
def saveConfig(predefs, filename):
    sectionNum = 0
    cp = CaseSensitiveConfigParser()
    for predef in predefs:
        sectionName = "Section" + str(sectionNum)
        sectionNum += 1
        cp.add_section(sectionName)
        cp.set(sectionName, "modelbase", predef.modelbase)
        cp.set(sectionName, "model", predef.std_model)
        cp.set(sectionName, "name", predef.name)
        cp.add_section(sectionName + ".modelbaseparameter")
        for (key, value) in predef.modelbaseParameter.items():
            cp.set(sectionName + ".modelbaseparameter", key, value)
        subSectionNum = 0
        for (model, mph) in predef.models.items():
            subSectionName = sectionName + ".modelparameters" +\
                str(subSectionNum)
            cp.add_section(subSectionName)
            cp.set(sectionName, "modelparameters" + str(subSectionNum), model)
            subSectionNum += 1
            for (key, value) in mph.items():
                cp.set(subSectionName, key, ",".join([y.replace("\\", "\\\\").\
                    replace(",", "\\.") for y in value]))
    f = open(filename, "w")
    cp.write(f)
    f.close()
    
def loadConfig(filename, databases):
    cp = CaseSensitiveConfigParser()
    cp.read(filename)
    Result = list()
    for section in filter(lambda x: "." not in x, cp.sections()):
        predef = modelConfiguration(cp.get(section, "name"))
        predef.modelbase = cp.get(section, "modelbase")
        if cp.has_section(section + ".modelbaseparameter"):
            predef.modelbaseParameter = dict(cp.items(section +\
                ".modelbaseparameter"))
        else:
            predef.modelbaseParameter = dict()
        predef.std_model = cp.get(section, "model")
        for modelNum in filter(lambda x: x.startswith("modelparameters"),
            cp.options(section)):
              if cp.has_section(section + "." + modelNum):
                  modelParameters = dict()
                  for (key, value) in cp.items(section + "." + modelNum):
                      modelParameters[key] = map(lambda s: s.replace("\\\\",
                          "\\,").replace("\\.", ",").replace("\\,", "\\"),
                          value.split(","))
                  predef.models[cp.get(section, modelNum)] = modelParameters
        Result.append(predef)
    return Result

class ModelDialog(gtke.AssistantDialog):
    def __init__(self, databases, predefdb):
        gtke.AssistantDialog.__init__(self)
        self.predefdb = predefdb
        self.databases = databases
        self.modelbase = None
        self.modelbaseoptions = None
        self.model = None
        self.modeloptions = None
        self.modelpredef = None
        self.FrontPage = ModelbaseSelectionPage(self)
        ModelbaseParameterPage(self)
        ModelParameterSavePage(self)
        ModelSelectionPage(self)
        ModelParameterPage(self)
        self.FrontPage.preparePage()

class ModelbaseSelectionPage(gtke.AssistantVBox):
    def createPage(self):
        self.title = "Select database"
        self.actionButtons = (gtk.Button(stock=gtk.STOCK_DELETE),)
        self.actionButtons[0].connect("clicked", self.deleteSelection)
        self.PopupMenu = gtk.Menu()
        DeleteItem = gtk.ImageMenuItem(gtk.STOCK_DELETE)
        DeleteItem.connect("activate", self.deleteSelection)
        EditItem = gtk.ImageMenuItem(gtk.STOCK_EDIT)
        EditItem.connect("activate", self.editSelection)
        self.PopupMenu.append(DeleteItem)
        self.PopupMenu.append(EditItem)
        DeleteItem.show()
        EditItem.show()
        dbs = map(lambda x: (x.name, x), self.assistant.predefdb)
        dbs.sort()
        self.dbtypes = dict(zip(map(lambda x: "new " + x + " configuration",
            map(getObjectName, self.assistant.databases)),
            self.assistant.databases))
        if len(dbs) > 0:
            dbs.append((None, None))
        dbs.extend(self.dbtypes.items())
        for widget in self.get_children():
            widget.destroy()
        self.dbchooser = gtke.createStringListView("Databases", dbs,
            treeviewProperties={"headers-visible":False, "enable-search":True})
        self.dbchooser.set_vadjustment(gtk.Adjustment())
        self.dbchooser.show()
        self.dbchooser.get_selection().connect("changed", self.selectionChanged)
        self.dbchooser.connect("button-press-event", self.dbchooserClick)
        self.dbchooser.connect("row-activated", self.dbchooserRowActivated)
        self.pack_start(self.dbchooser)
        self.show()
        self.selectionChanged(self.dbchooser.get_selection())
        
    def pageFinished(self):
        choice = self.dbchooser.getSelectedUserData()
        self.assistant.model = None
        self.assistant.modeloptions = None
        if choice in self.dbtypes.values():
            self.assistant.modelbase = choice
            self.assistant.modelpredef = None
            self.assistant.modelbaseoptions = None
        else:
            modelbaseclass = choice.getModelbaseClass(self.dbtypes.values())
            self.assistant.modelpredef = choice
            self.assistant.modelbase = modelbaseclass
            self.assistant.modelbaseoptions = choice.modelbaseParameter
    
    def selectionChanged(self, tvs):
        "Set status of the next and delete button"
        sud = gtke.TreeView_getSelectedUserData(tvs.get_tree_view())
        self.actionButtons[0].set_sensitive(isinstance(sud, modelConfiguration))
        if sud != None:
            if isinstance(sud, modelConfiguration) and sud.getModelbaseClass(
                self.dbtypes.values()) == None:
                    sud = None
            elif (sud in self.dbtypes.values()):
                self.setPageSkip(0)
            else:
                self.setPageSkip(2)
        self.assistant.set_page_complete(self, (tvs.count_selected_rows() > 0)\
            and (sud != None))

        
    def deleteSelection(self, sender):
        """Called when the user presses either the delete button or chooses
        delete from the menu"""
        self.assistant.predefdb.remove(self.dbchooser.getSelectedUserData())
        self.dbchooser.get_model().remove(self.dbchooser.get_selection().\
        get_selected()[1])
        
    def editSelection(self, sender):
        "Called when the user selects edit from the popup menu"
        self.setPageSkip(0)
        self.assistant.forward()
    
    def dbchooserClick(self, widget, event):
        "Show popup menu if the click was by the right mouse button"
        if (event.button == 3) and isinstance(widget.getUserDataAt(int(event.x),
            int(event.y)), modelConfiguration):
              self.PopupMenu.popup(None, None, None, event.button, event.time)
        return False
       
    def dbchooserRowActivated(self, treeview, path, view_column):
        self.assistant.forward()

class AbstractParameterPage(gtke.AssistantTable):
    """
    
    name:        Name of the variable
    label:       Label to be shown as name
    hidden:      if True, entry will be a password entry
    advanced:    if True this will be shown under advanced
    tip:         This text is shown as tooltip
    default:     Value to be entered into the entry
    omit:        if this expression evaluates to True, this variable won't be in
                 the resultlist
    assert:      Single expression which must evaluate to True in order to
                 validate this variable (can also be a list)
    asserterror: Message to be shown if any assertion evaluates to False
    """
    
    def createPage(self):
        for widget in self.get_children():
            widget.destroy()
        db = self.getBase()
        self.Parameters = self.getParameters()
        tooltips = gtk.Tooltips()
        # Check if gladefile is present
        if "parameterGladefile" in dir(db):
            gladefile = db.parameterGladefile
            if callable(gladefile):
                gladefile = gladefile()
            glade = gtk.glade.XML(*gladefile)
            self.attach(glade.get_widget(gladefile[1]), 0, 1, 0, 1)
            for var in self.Parameters: 
                var["widgets"] = glade.get_widget_prefix(var["name"])
                if var["widgets"] == None:
                    var["widgets"] = list()
                var["entry"] = glade.get_widget(var["name"])
                var["entry"].connect("activate", self.entryActivated)
            #connect event-handlers of db kiwi-style
            for attrib in dir(db):
                if attrib[:3] == "on_":
                    pos = attrib.find("__", 3)
                    widget_name = attrib[3:pos]
                    signal_name = attrib[pos + 2:]
                    widget = glade.get_widget(widget_name)
                    if widget != None:
                        widget.connect(signal_name, getattr(db, attrib))
                if attrib[:6] == "after_":
                    pos = attrib.find("__", 6)
                    widget_name = attrib[6:pos]
                    signal_name = attrib[pos + 2:]
                    widget = glade.get_widget(widget_name)
                    if widget != None:
                        widget.connect_after(signal_name, getattr(db, attrib))
        else:
            row = 0
            advRow = 0
            advancedExpander = gtk.Expander("Advanced")
            advancedTable = gtk.Table()
            advancedExpander.add(advancedTable)
            for var in self.Parameters:
                label = gtk.Label(var.get("label", var["name"]))
                label.set_alignment(1.0, 0.5)
                if var.has_key("history"):
                    edit = gtke.EntryWithCompletition(var["history"])
                else:
                    edit = gtk.Entry()
                if var.has_key("default"):
                    edit.set_text(var["default"])
                edit.set_visibility(not var.get("hidden", False))
                edit.connect("changed", self.checkAssertions)
                edit.connect("activate", self.entryActivated)
                var["entry"] = edit
                var["widgets"] = [label, edit]
                if var.get("advanced", False):
                    advancedTable.attach(label, 0, 1, advRow, advRow + 1,
                        gtk.FILL, gtk.FILL, 2, 2)
                    advancedTable.attach(edit, 1, 2, advRow, advRow + 1,
                        gtk.FILL|gtk.EXPAND, gtk.FILL, 2, 2)
                    advRow += 1
                else:
                    self.attach(label, 0, 1, row, row + 1, gtk.FILL, gtk.FILL,
                        2, 2)
                    self.attach(edit, 1, 2, row, row + 1, gtk.FILL|gtk.EXPAND,
                        gtk.FILL, 2, 2)
                    row += 1
                if var.has_key("tip"):
                    tooltips.set_tip(label, var["tip"])
            if advRow > 0:
                self.attach(advancedExpander, 0, 2, row, row + 1, gtk.FILL | 
                    gtk.EXPAND, gtk.FILL, 2, 2)
            else:
                advancedExpander.destroy()
        self.statusLabelEB = gtk.EventBox()
        self.statusLabel = gtk.Label()
        self.statusLabelEB.add(self.statusLabel)
        self.statusLabelEBNormalColor = self.statusLabelEB.get_style().bg[0]
        self.statusLabelEBErrorColor = self.statusLabelEB.get_colormap().\
            alloc_color("red")
        self.attach(self.statusLabelEB, 0, self.get_property("n-columns"),
            self.get_property("n-rows"), self.get_property("n-rows") + 1,
            gtk.EXPAND|gtk.SHRINK|gtk.FILL, gtk.FILL)
        self.checkAssertions()
            
    def checkAssertions(self, *args):
        Resultset = dict()
        for var in self.Parameters:
            Resultset.update({var["name"]:var["entry"].get_text()})
            assertions = var.get("assert", None)
            if isinstance(assertions, str):
                assertions = (assertions,)
            if assertions != None:
                for cond in assertions:
                    if not eval(cond, None, Resultset):
                        self.assistant.set_page_complete(self, False)
                        self.statusLabel.set_text(var.get("asserterror", cond))
                        self.statusLabelEB.modify_bg(gtk.STATE_NORMAL,
                            self.statusLabelEBErrorColor)
                        return
        self.assistant.set_page_complete(self, True)
        self.statusLabelEB.modify_bg(gtk.STATE_NORMAL,
            self.statusLabelEBNormalColor)
        self.statusLabel.set_text("Settings are ok")

    def getResult(self):
        Resultset = dict()
        for var in self.Parameters:
            if var.get("single", True):
                Resultset.update({var["name"]:var["entry"].get_text()})
            elif var["entry"] != None:
                for param in self.Parameters[-1]["entry"].get_text().split(","):
                    addi = param.split("=", 1)
                    if len(addi) == 2:
                        Resultset[addi[0].strip()] = addi[1].strip()
        todelete = list()
        for var in self.Parameters:
            if var.has_key("omit") and eval(var["omit"], None, Resultset):
                todelete.append(var["name"])
        for name in todelete:
            del Resultset[name]
        return Resultset
    
    def entryActivated(self, entry):
        self.assistant.forward()
        
class ModelbaseParameterPage(AbstractParameterPage):
    title = "Enter database parameters"
    def getBase(self):
        return self.assistant.modelbase

    def getParameters(self):
        Result = getParameterInfo(self.assistant.modelbase)
        additional = str()
        if self.assistant.modelbaseoptions != None:
            lookup = dict(map(lambda x: (x["name"], x), Result))
            for (key, value) in self.assistant.modelbaseoptions.items():
                try:
                    lookup[key]["default"] = value
                except KeyError:
                    additional += ", " + key + "=" + value
            additional = additional[1:] #remove leading comma
        Result.append({"name":"__additional__",
                       "label":"Additional Parameters",
                       "advanced":True,
                       "tip":"Enter additional parameters not displayed above"
                             " here",
                       "single":False,
                       "default":additional})
        return Result
  
    def pageFinished(self):
        self.assistant.modelbaseoptions = self.getResult()
        self.assistant.model = None
        self.assistant.modeloptions = None
        if self.assistant.modelpredef != None:
            self.assistant.modelpredef.modelbaseParameter =\
                self.assistant.modelbaseoptions


class ModelParameterSavePage(gtke.AssistantVBox):
    def createPage(self):
        for widget in self.get_children():
            widget.destroy()
        self.title = "Save settings"
        self.actionButtons = (gtk.Button(stock=gtk.STOCK_DELETE),)
        self.actionButtons[0].connect("clicked", self.deleteSelection)
        self.PopupMenu = gtk.Menu()
        DeleteItem = gtk.ImageMenuItem(gtk.STOCK_DELETE)
        DeleteItem.connect("activate", self.deleteSelection)
        self.PopupMenu.append(DeleteItem)
        DeleteItem.show()
        self.predefs = map(lambda x: x.name, self.assistant.predefdb)
        try:
            self.predefs.remove(self.assistant.modelpredef.name)
        except (ValueError, AttributeError):
          pass
        self.predefs.sort()
        self.predeflist = gtke.createStringListView("Databases", self.predefs,
            treeviewProperties={"headers-visible":False, "enable-search":True})
        self.predeflist.set_vadjustment(gtk.Adjustment())
        self.predeflist.connect("button-press-event", self.dbchooserClick)
        self.pack_start(gtk.Label("used names"), True, False)
        self.pack_start(self.predeflist, True, True)
        self.pack_start(gtk.Label("name current settings to save"), True, False)
        self.nameEntry = gtk.Entry()
        if self.assistant.modelpredef != None:
            self.nameEntry.set_text(self.assistant.modelpredef.name)
        self.nameEntry.connect("changed", self.checkName)
        self.nameEntry.connect("activate", self.nameActivate)
        self.pack_start(self.nameEntry, True, False)
        self.statusLabel = gtk.Label()
        self.pack_start(self.statusLabel, True, False, 2)
        self.checkName()
        self.nameEntry.grab_focus()

    def checkName(self, *args):
        text = self.nameEntry.get_text()
        if text == "":
            self.statusLabel.set_text("Currently the settings will not be saved")
            self.assistant.set_page_complete(self, True)
        elif text in self.predefs:
            self.statusLabel.set_text("This name is already in use")
            self.assistant.set_page_complete(self, False)
        else:
            self.statusLabel.set_text("The settings will be saved as " + text)
            self.assistant.set_page_complete(self, True)
            
    def pageFinished(self):
        name = self.nameEntry.get_text()
        if self.assistant.modelpredef != None:
            self.assistant.predefdb.remove(dict(map(lambda x: (x.name, x),
                self.assistant.predefdb)).get(self.assistant.modelpredef.name))
        if name != "":
            self.assistant.modelpredef = modelConfiguration(name, getObjectName(
             self.assistant.modelbase), self.assistant.modelbaseoptions, dict())
        else:
            self.assistant.modelpredef = None

    def dbchooserClick(self, widget, event):
        "Show popup menu if the click was by the right mouse button"
        if (event.button == 3):
            self.PopupMenu.popup(None, None, None, event.button, event.time)
        return False

    def deleteSelection(self, sender):
        """Called when the user presses either the delete button or chooses
        delete from the menu"""
        self.assistant.predefdb.remove(dict(map(lambda predef: (predef.name,
            predef), self.assistant.predefdb)).get(self.predeflist.\
            getSelectedValue()))
        self.predeflist.get_model().remove(self.predeflist.get_selection().\
            get_selected()[1])
        
    def nameActivate(self, entry):
        "Called when enter is pressed on the name entry"
        self.assistant.forward()

class ModelSelectionPage(gtke.AssistantVBox):
    def createPage(self):
        for widget in self.get_children():
            widget.destroy()
        self.title = "Select model"
        models = map(lambda db: (getObjectName(db), db), getDBModels(self.\
            assistant.modelbase, self.assistant.modelbaseoptions).values())
        self.modelchooser = gtke.createStringListView("Models", models,
            treeviewProperties={"headers-visible":False, "enable-search":True})
        self.modelchooser.set_vadjustment(gtk.Adjustment())
        self.pack_start(self.modelchooser)
        self.modelchooser.get_selection().connect("changed",
            self.selectionChanged)
        self.modelchooser.connect("row-activated",
            self.modelchooserRowActivated)
        if (self.assistant.modelpredef != None) and \
            (self.assistant.modelpredef.std_model != None):
                self.modelchooser.selectByValue(self.assistant.\
                    modelpredef.std_model)
        self.selectionChanged(self.modelchooser.get_selection())

    def selectionChanged(self, tvs):
        self.assistant.set_page_complete(self, tvs.count_selected_rows() > 0)
        if tvs.count_selected_rows() > 0:
            self.assistant.set_page_complete(self, True)
            model = self.modelchooser.getSelectedUserData()
            if (model != None) and (len(getParameterInfo(model)) > 0):
                self.setPageSkip(0)
                self.page_type = gtk.ASSISTANT_PAGE_CONTENT
            else:
                self.page_type = gtk.ASSISTANT_PAGE_CONFIRM
                self.setPageSkip(1)
        else:
            self.assistant.set_page_complete(self, False)
            self.setPageSkip(0)
            self.page_type = gtk.ASSISTANT_PAGE_CONTENT
        
    def modelchooserRowActivated(self, treeview, path, view_column):
        self.assistant.forward()
    
    def pageFinished(self):
        self.assistant.model = self.modelchooser.getSelectedUserData()
        self.assistant.modeloptions = None
        if self.assistant.modelpredef != None:
            self.assistant.modelpredef.std_model = getObjectName(self.\
                assistant.model)


class ModelParameterPage(AbstractParameterPage):
    page_type = gtk.ASSISTANT_PAGE_CONFIRM
    title = "Enter model parameters"
    MAX_HISTORY_LIST_LENGTH = 10
    def getBase(self):
        return self.assistant.model

    def getParameters(self):
        #check for model == None, may happen, when call to createPage happens
        #before actually showing it
        if self.assistant.model != None:
            Result = getParameterInfo(self.assistant.model)
        else:
            return list()
        # merge saved values from predef into Result
        if self.assistant.modelpredef != None and self.assistant.modelpredef.\
            models.has_key(getObjectName(self.assistant.model)):
              pre = self.assistant.modelpredef.models[getObjectName(self.\
                  assistant.model)]
              for var in Result:
                  if pre.has_key(var["name"]):
                      var["history"] = pre[var["name"]]
                      if len(var["history"]) > 0:
                          var["default"] = var["history"][0]
        return Result
  
    def pageFinished(self):
        self.assistant.modeloptions = self.getResult()
        pre = self.assistant.modelpredef
        if pre != None:
            modelname = getObjectName(self.assistant.model)
            options = pre.models.get(modelname, dict())
            for (name, value) in self.assistant.modeloptions.items():
                lst = options.get(name, list())
                if value in lst:
                    lst.remove(value)
                lst.insert(0, value)
                while len(lst) > self.MAX_HISTORY_LIST_LENGTH:
                    lst.pop()
                options[name] = lst
            pre.models[modelname] = options
        
def getModel(parent=None, showall=False):
    databases = getModelBases()
    predefs = loadConfig(getCFGFilename("relrdf") + "models", databases)
    md = ModelDialog(databases.values(), predefs)
    if not md.run(parent, showall):
        md.destroy()
        return False
    if md.modelpredef != None:
        md.predefdb = filter(lambda predef: predef.name != md.modelpredef.name,
            md.predefdb)
        md.predefdb.append(md.modelpredef)
    saveConfig(md.predefdb, getCFGFilename("relrdf") + "models")
    Result = [dict([(y, x) for (x, y) in databases.items()]).get(md.modelbase,
        None), md.modelbaseoptions, dict([(y, x) for (x, y) in getDBModels(
        md.modelbase, md.modelbaseoptions).items()]).get(md.model, None),
        md.modeloptions]
    if Result[1] == None:
        Result[1] = dict()
    if Result[3] == None:
        Result[3] = dict()
    md.destroy()
    return Result

if __name__ == "__main__":
    import pygtk
    pygtk.require("2.0")

    print getModel()
