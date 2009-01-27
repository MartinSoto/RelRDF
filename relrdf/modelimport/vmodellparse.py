# -*- coding: utf-8 -*-

import sys
import urllib

from xml.parsers import expat

from relrdf import commonns
from relrdf.expression import literal, uri
from relrdf.basesinks import PrintSink


vModellNs = uri.Namespace('http://www.v-modell-xt.de/schema/1#')


class VModellElem(object):
    """Information pertaining to one XML element of the V-Modell
    hierarchy."""

    __slots__ = ('name',
                 'uri')

    def __init__(self):
        self.uri = None
        self.name = None


class VModellParser(object):
    """A parser for the XML representation of the V-Modell XT, that
    generates an equivalent RDF representation."""

    __slots__ = ('namespace',
                 'sink',
                 'elems',
                 'currentElem',
                 'acumText')


    # Elements lacking an id attribute, which means their id must be
    # generated from their name property.
    nameIdElems = set(('Begriffsabbildung',))

    # Elements that must be excluded because they are unnecessary in
    # the RDF representation.
    excludedElements = set((
            u'Abkürzungen',
            u'Ablaufbausteine',
            u'Ablaufbausteinspezifikationen',
            u'AbstrakteModellElemente',
            u'Aktivitäten',
            u'Aktivitätsbeziehungen',
            u'Aktivitätsgruppen',
            u'Beziehungen',
            u'Disziplinen',
            u'Entscheidungspunkte',
            u'ErzeugendeAbhängigkeiten',
            u'ErzeugendeAbhängigkeitserweiterungen',
            u'ExterneKopiervorlagen',
            u'Glossar',
            u'InhaltlicheAbhängigkeiten',
            u'InhaltlicheAbhängigkeitserweiterungen',
            u'Konventionsabbildungen',
            u'Methodenreferenzen',
            u'Produktabhängigkeiten',
            u'Produktabhängigkeitsbeziehungen',
            u'Produktabhängigkeitsbeziehungen',
            u'Produktbeziehungen',
            u'Produkte',
            u'Produktgruppen',
            u'Projektdurchführungsstrategien',
            u'Projektmerkmale',
            u'Projekttypen',
            u'Projekttypvarianten',
            u'Quellen',
            u'Rollen',
            u'Rollenbeziehungen',
            u'Strukturabhängigkeiten',
            u'Strukturabhängigkeitserweiterungen',
            u'Tailoringabhängigkeiten',
            u'Teilaktivitäten',
            u'Textbausteine',
            u'Themen',
            u'V-Modell-Struktur',
            u'Vorgehensbausteine',
            u'Werkzeugreferenzen',
            ))

    # Element attributes excluded when created RDF properties. This
    # may be because they are unnecessary or redundant in the RDF
    # representation.
    excludedAttributes = set((
            'id',
            'link',
            'version',
            'consistent_to_version',
            'refers_to_id',
            ))


    # The dummy value used to mark name id elements.
    NAME_ID_URI = '<<Name ID>>'


    def __init__(self, fileObj,
                 namespace=uri.Namespace('http://www.v-modell-xt.de/'
                                         'model/1#'),
                 sink=None):
        self.namespace = namespace

        if sink is None:
            self.sink = PrintSink()
        else:
            self.sink = sink

        self.elems = []
        self.currentElem = None

        self.acumText = None

        p = expat.ParserCreate()

        p.StartElementHandler = self._startElementHandler
        p.EndElementHandler = self._endElementHandler
        p.CharacterDataHandler = self._characterDataHandler

        p.ParseFile(fileObj)

    def _startElementHandler(self, name, attributes):
        if self.acumText is not None:
            self.warning('Mixed content')

        elem = self._pushElem(name, attributes)

        if 'link' in attributes:
            # We have a relation between objects.
            value = self.namespace['id' + attributes['link']]

            if len(self.elems) >= 2 and \
                   self.elems[-2].uri is not None:
                # The relation refers to the containing level.
                propertyName = elem.name
            elif len(self.elems) >= 3 and \
                     self.elems[-3].uri is not None:
                # The relation refers to the object two levels up.
                propertyName = self.elems[-2].name
            else:
                self.warning('Cannot find property for link')
                propertyName = 'unknown'

            # Create a property for the relation.
            self._addProperty(propertyName, value)

        for name, value in attributes.items():
            if name not in self.excludedAttributes and ':' not in name:
                # Make a property.
                self._addProperty(name, literal.Literal(value))

    def _endElementHandler(self, name):
        elem = self._popElem()

        if elem.uri is not None:
            # Create a declaration for the object.
            self.sink.triple(elem.uri, commonns.rdf.type,
                             uri.Uri(vModellNs[elem.name]))

            # If there is a containing object, create a 'contains'
            # relationship that reflects the structure.

            parent = None
            for superelem in reversed(self.elems):
                if superelem.uri is not None:
                    parent = superelem
                    break

            if parent is not None:
                self.sink.triple(parent.uri,
                                 uri.Uri(vModellNs[u'enthält']),
                                 elem.uri)

        if self.acumText is not None:
            # Add a property to the current object.
            self._addProperty(elem.name, literal.Literal(self.acumText))
            self.acumText = None

            if self.elems[-1] != self.currentElem:
                self.warning("property '%s' is not directly contained in"
                             " current element '%s'" % \
                             (name, self.currentElem.name))

    def _characterDataHandler(self, data):
        if data != '' and not data.isspace():
            if self.acumText is None:
                self.acumText = data
            else:
                self.acumText += data

    def _pushElem(self, name, attributes):
        elem = VModellElem()
        elem.name = name
        self.elems.append(elem)

        if len(self.elems) == 1:
            # We associate a special URI to the whole model.
            id = 'root'
            elem.uri = self.namespace[id]
        elif name not in self.excludedElements:
            if 'id' in attributes:
                id = attributes['id']
                elem.uri = self.namespace['id' + id]
            elif name in self.nameIdElems:
                # Give the element a dummy URI which will be replaced
                # as soon as a we see its name property.
                elem.uri = self.NAME_ID_URI

        self._updateCurrent()

        return elem

    def _popElem(self):
        elem = self.elems.pop()
        if len(self.elems) > 0:
            self._updateCurrent()
        return elem

    def _updateCurrent(self):
        for elem in reversed(self.elems):
            if elem.uri is not None:
                self.currentElem = elem
                return

        # In the worst case, the first element of the list should have
        # an URI.
        assert False

    def _addProperty(self, propertyName, value):
        if self.currentElem.uri == self.NAME_ID_URI:
            if propertyName != 'Name':
                self.warning("property '%s' from '%s' seen, but no id"
                             " is available" % \
                             (propertyName, self.currentElem.name))
                return
            self.currentElem.uri = self.namespace['id' +
                                                  urllib.quote(unicode(value) \
                                                               .encode('utf-8'))]
                
        self.sink.triple(self.currentElem.uri, vModellNs[propertyName],
                         value)

    def warning(self, msg):
        print >> sys.stderr, "Warning:", msg.encode('utf-8')


if __name__ == '__main__':
    VModellParser(sys.stdin)
