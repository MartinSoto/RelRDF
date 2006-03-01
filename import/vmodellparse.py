import sys

from xml.dom import pulldom

import commonns
from expression import literal, uri
from basesinks import PrintSink


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
                 'currentElem')

    def __init__(self, fileName,
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

        text = None

        for event, node in pulldom.parse(fileName):
            if event == 'START_ELEMENT':
                if text is not None:
                    self.warning('Mixed content')

                elem = self._pushElem(node)

                if elem.uri is not None:
                    # Create a declaration for the object.
                    self.sink.triple(elem.uri, commonns.rdf.type,
                                     literal.Literal(vModellNs[elem.name]))

                if node.hasAttribute('link'):
                    # We have a relation between objects.
                    value = self.namespace[node.getAttribute('link')]

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

                for i in range(node.attributes.length):
                    attrib = node.attributes.item(i)
                    if attrib.name != 'id' and attrib.name != 'link':
                        # Make a property.
                        self._addProperty(attrib.name,
                                          literal.Literal(attrib.value))

            elif event == 'END_ELEMENT':
                elem = self._popElem()

                if text is not None:
                    # Add a property to the current object.
                    self._addProperty(elem.name, literal.Literal(text))
                    text = None

            elif event == 'CHARACTERS':
                value = node.nodeValue
                if value != '' and not value.isspace():
                    if text is None:
                        text = value
                    else:
                        text += value

    def _pushElem(self, node):
        elem = VModellElem()
        elem.name = node.nodeName
        self.elems.append(elem)

        if node.hasAttribute('id'):
            id = node.getAttribute('id')
            elem.uri = self.namespace[id]
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
    VModellParser(sys.argv[1])
