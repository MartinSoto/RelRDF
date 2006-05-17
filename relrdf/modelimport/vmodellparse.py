import sys

from xml.parsers import expat

from relrdf import commonns
from relrdf.expression import literal, uri
from relrdf.basesinks import PrintSink


vModellNs = uri.Namespace('http://www.v-modell.iabg.de/Schema#')


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

    def __init__(self, fileObj,
                 namespace=uri.Namespace('http://www.kbst.bund.de/'
                                         'V-Modell-XT.xml#'),
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

        if elem.uri is not None:
            # Create a declaration for the object.
            self.sink.triple(elem.uri, commonns.rdf.type,
                             uri.Uri(vModellNs[elem.name]))

            parent = None
            for superelem in reversed(self.elems[:-1]):
                if superelem.uri is not None and \
                   superelem.name != 'V-Modell':
                    parent = superelem
                    break

            if parent is not None:
                self.sink.triple(parent.uri,
                                 uri.Uri(vModellNs['%s_enthaelt_%s' \
                                                   % (parent.name,
                                                      elem.name)]),
                                 elem.uri)

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
            if name != 'id' and name != 'link' and ':' not in name:
                # Make a property.
                self._addProperty(name, literal.Literal(value))

    def _endElementHandler(self, name):
        elem = self._popElem()

        if self.acumText is not None:
            # Add a property to the current object.
            self._addProperty(elem.name, literal.Literal(self.acumText))
            self.acumText = None

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

        if 'id' in attributes:
            id = attributes['id']
            elem.uri = self.namespace['id' + id]
        elif len(self.elems) == 1:
            # We associate a special URI to the whole model.
            id = 'root'
            elem.uri = self.namespace[id]

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
        self.sink.triple(self.currentElem.uri, vModellNs[propertyName],
                         value)

    def warning(self, msg):
        print >> sys.stderr, "Warning:", msg


if __name__ == '__main__':
    VModellParser(sys.stdin)
