import os
import cgi

import gtk

from kiwifixes import UiManagerSlaveDelegate

import pixmaps


class SchemaBrowser(UiManagerSlaveDelegate):

    popupGroup__actions = [('showInstances', None,
                            _('Show _Instances'), None, None)]

    uiDefinition = '''<ui>
    <popup name="classPopUp">
      <menuitem action="showInstances"/>
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

    def _searchEqual(self, model, column, key, itr):
        return not (key in str(model.get_value(itr, column)).lower())


    def on_classView__drag_data_get(self, widget, context, selection,
                                   targetType, eventTime):
        cls = self.getCurrentClass()
        selection.set(selection.target, 8,
                      self.shortener.shortenUri(cls).encode('utf-8'))

    # FIXME: This should be button_press but something in
    # Kiwi/Gazpacho seems to be trapping the event.
    def on_classView__button_release_event(self, widget, event):
        if event.button == 3:
            self.classPopUp.popup(None, None, None,
                                  event.button, event.time)

    def on_showInstances__activate(self, widget, *args):
        self.mainWindow.runQuery(
            "select instance\nfrom {instance} rdf:type {%s}" % \
            self.shortener.shortenUri(self.getCurrentClass()))
