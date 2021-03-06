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


import cgi

import gtk

from evolyzer.kiwifixes import UiManagerSlaveDelegate

import schema
import pixmaps


class PredefQuery(object):
    __slots__ = ()

    def isActive(self, classes, props):
        raise NotImplementedError

    def getQuery(self, classes, props):
        raise NotImplementedError


class GetInstancesQuery(PredefQuery):
    __slots__ = ()

    def isActive(self, classes, props):
        if len(classes) != 1:
            return False

        cls = classes[0]
        outgoing = cls.getAllOutgoingProps()
        incoming = cls.getAllIncomingProps()

        for prop in props:
            if not prop in outgoing and \
               not prop in incoming:
                return False

        return True

    @staticmethod
    def makeVarName(propShort, varNames):
        if propShort[0] == '<':
            varName = '?prop'
        else:
            chrs = list(propShort)
            for i, c in enumerate(chrs):
                if not c.isalnum():
                    chrs[i] = '_'

            if not chrs[0].isalpha():
                varName = '?prop_' + ''.join(chrs)
            else:
                varName = '?' + ''.join(chrs)

        if varName in varNames:
            i = 1
            while '%s%d' % (varName, i) in varNames:
                i += 1
            varName = '%s%d' % (varName, i)

        varNames.append(varName)

        return varName

    def getQuery(self, classes, props, shortener):
        cls = classes[0]
        outgoing = cls.getAllOutgoingProps()
        incoming = cls.getAllIncomingProps()

        varNames = ['?inst']
        propClauses = []
        for prop in props:
            short = shortener.shortenUri(prop)

            if prop in outgoing:
                varName = self.makeVarName(short, varNames)
                propClauses.append("  optional {\n    ?inst %s %s\n  }\n" %
                                   (short, varName))
            
            if prop in incoming:
                varName = self.makeVarName(short + '_pred', varNames)
                propClauses.append("  optional {\n    %s %s ?inst\n  }\n" %
                                   (varName, short))

        return "select %s\nwhere {\n  ?inst rdf:type %s\n%s}" % \
            (' '.join(varNames), shortener.shortenUri(cls),
             ''.join(propClauses))


class CompInstancesQuery(GetInstancesQuery):
    __slots__ = ()

    def getQuery(self, classes, props, shortener):
        cls = classes[0]
        outgoing = cls.getAllOutgoingProps()
        incoming = cls.getAllIncomingProps()

        varNames = ['?comp', '?inst']
        propClauses = []
        for prop in props:
            short = shortener.shortenUri(prop)

            if prop in outgoing:
                varName = self.makeVarName(short, varNames)
                propClauses.append("  optional { graph relrdf:compAB "
                                   "{?inst %s %s} }\n" %
                                   (short, varName))
            
                varName = self.makeVarName(short + '_old', varNames)
                propClauses.append("  optional { graph relrdf:compA "
                                   "{?inst %s %s} }\n" %
                                   (short, varName))
            
                varName = self.makeVarName(short + '_new', varNames)
                propClauses.append("  optional { graph relrdf:compB "
                                   "{?inst %s %s} }\n" %
                                   (short, varName))
            
            if prop in incoming:
                varName = self.makeVarName(short + '_pred', varNames)
                propClauses.append("  optional { graph relrdf:compAB "
                                   "{ %s %s ?inst} }\n" %
                                   (varName, short))

                varName = self.makeVarName(short + '_pred_old', varNames)
                propClauses.append("  optional { graph relrdf:compA "
                                   "{ %s %s ?inst} }\n" %
                                   (varName, short))

                varName = self.makeVarName(short + '_pred_new', varNames)
                propClauses.append("  optional { graph relrdf:compB "
                                   "{ %s %s ?inst} }\n" %
                                   (varName, short))

        return "select %s\nwhere {\n  graph ?comp {?inst rdf:type %s}\n%s}" % \
            (' '.join(varNames), shortener.shortenUri(cls),
             ''.join(propClauses))    


class SchemaBrowser(UiManagerSlaveDelegate):

    popupGroup__actions = [('showInstProp', None,
                            _('Show instances & properties'), None, None),
                           ('compInstProp', None,
                            _('Compare instances & properties'), None, None)]

    uiDefinition = '''<ui>
    <popup name="classPopUp">
      <menuitem action="showInstProp"/>
      <menuitem action="compInstProp"/>
    </popup>
    </ui>'''

    def __init__(self):
        UiManagerSlaveDelegate.__init__(self, gladefile="browser",
                                        toplevel_name='schemaBrowser')
        self.mainWindow = None

        # Render the icons once for use in the list.
        self.forwardPixbuf = self.classView.render_icon(gtk.STOCK_GO_FORWARD,
                                                        gtk.ICON_SIZE_MENU )
        self.backwardPixbuf = self.classView.render_icon(gtk.STOCK_GO_BACK,
                                                         gtk.ICON_SIZE_MENU )

        # Set up the browser.
        self.classView.set_headers_visible(False)

        self.nodeCol = gtk.TreeViewColumn()
        self.classView.append_column(self.nodeCol)

        pixbufRenderer = gtk.CellRendererPixbuf()
        self.nodeCol.pack_start(pixbufRenderer, False)
        self.nodeCol.add_attribute(pixbufRenderer, 'pixbuf', 1)

        textRenderer = gtk.CellRendererText()
        self.nodeCol.pack_start(textRenderer, True)
        self.nodeCol.add_attribute(textRenderer, 'markup', 2)

        self.classTS = None

        # Allow multiple selection.
        self.classView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        # Enable searching. The fourth column in the model is special
        # for this purpose.
        self.classView.set_enable_search(True)
        self.classView.set_search_column(0)
        self.classView.set_search_equal_func(self._searchEqual)

        # The class browser's popup menu.
        self.classPopUp = self.uiManager.get_widget('/classPopUp')

        # Allow dragging from the class view.
        self.classView.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK,
            [('UTF8_STRING', 0, 0)],
            gtk.gdk.ACTION_COPY)

        # Predefined queries.
        self.predefGetInstances = GetInstancesQuery()
        self.predefCompInstances = CompInstancesQuery()

        # Connect the button press signal manually, since Kiwi seems
        # to fail doing it properly.
        self.classView.connect('button-press-event',
                               self.on_classView__button_press_event)

    def setMainWindow(self, mainWindow):
        self.mainWindow = mainWindow
        self.classPopUp.mainWindow = mainWindow

    def setSchema(self, schema, shortener):
        self.schema = schema
        self.shortener = shortener

        # Columns: Class/property object, icon, formatted name.
        self.classTS = gtk.TreeStore(object, gtk.gdk.Pixbuf, str)

        clsList = self.schema.classes.values()
        clsList.sort(key=str)
        for cls in clsList:
            self.addRdfClass(cls)

        self.classView.set_model(self.classTS)

    def addRdfClass(self, rdfClass):
        parent = self.classTS. \
                 append(None, [rdfClass, pixmaps.classPixbuf,
                               '<b>%s</b>' %
                               self._prepareUri(rdfClass)])

        propList = list(rdfClass.getAllOutgoingProps())
        propList.sort(key=str)
        for p in propList:
            if len(p.range) == 0:
                # This is funny, but we can show the property anyway.
                self.classTS.append(parent,
                                    [p, self.forwardPixbuf,
                                     '<b>%s</b> ?' %
                                     self._prepareUri(p)])
            else:
                for r in p.range:
                    self.classTS.append(parent,
                                        [p, self.forwardPixbuf,
                                         '<b>%s</b> %s' %
                                         (self._prepareUri(p),
                                          self._prepareUri(r))])

        propList = list(rdfClass.getAllIncomingProps())
        propList.sort(key=str)
        for p in propList:
            if len(p.domain) == 0:
                # This is funny, but we can show the property anyway.
                self.classTS.append(parent,
                                    [p, self.forwardPixbuf,
                                     '? <b>%s</b>' %
                                     self._prepareUri(p)])
            else:
                for r in p.domain:
                    self.classTS.append(parent,
                                        [p, self.backwardPixbuf,
                                         '%s <b>%s</b>' %
                                         (self._prepareUri(r),
                                          self._prepareUri(p))])

    def _prepareUri(self, rdfClass):
        return cgi.escape(self.shortener.shortenUri(rdfClass.getUri()))

    def getCurrentClass(self):
        (path, col) = self.classView.get_cursor()
        tItr = self.classTS.get_iter(path)
        (cls,) = self.classTS.get(tItr, 0)
        return cls

    def getSelectedElems(self):
        model, pathList = self.classView.get_selection().get_selected_rows()

        classes = []
        props = []
        for path in pathList:
            itr = self.classTS.get_iter(path)
            obj, = self.classTS.get(itr, 0)
            if isinstance(obj, schema.RdfClass):
                classes.append(obj)
            elif isinstance(obj, schema.RdfProperty):
                props.append(obj)

        return (classes, props)

    def checkPredefQueries(self):
        classes, props = self.getSelectedElems()
        self.showInstProp.set_sensitive(self.predefGetInstances. \
                                         isActive(classes, props))
        self.compInstProp.set_sensitive(self.predefCompInstances. \
                                         isActive(classes, props))

    def _searchEqual(self, model, column, key, itr):
        return not (key in str(model.get_value(itr, column)).lower())


    def on_classView__drag_data_get(self, widget, context, selection,
                                   targetType, eventTime):
        cls = self.getCurrentClass()
        selection.set(selection.target, 8,
                      self.shortener.shortenUri(cls).encode('utf-8'))

    # This signal handler must be connected manually. See the __init__
    # method.
    def on_classView__button_press_event(self, widget, event):
        if event.button == 3:
            clicked = widget.get_path_at_pos(int(event.x), int(event.y))
            if clicked == None: return False  # No Item clicked -> Let GTK handle
            selection = widget.get_selection()
            if not (selection.path_is_selected(clicked[0])):
                if not(event.get_state() & gtk.gdk.CONTROL_MASK): selection.unselect_all()
                selection.select_path(clicked[0])
            
            self.checkPredefQueries()
            self.classPopUp.popup(None, None, None,
                                  event.button, event.time)

            # Prevent the button press from changing the selection.
            return True

    def on_showInstProp__activate(self, widget, *args):
        classes, props = self.getSelectedElems()
        self.mainWindow.runQuery(self.predefGetInstances. \
                                 getQuery(classes, props, self.shortener))

    def on_compInstProp__activate(self, widget, *args):
        classes, props = self.getSelectedElems()
        self.mainWindow.runQuery(self.predefCompInstances. \
                                 getQuery(classes, props, self.shortener))
