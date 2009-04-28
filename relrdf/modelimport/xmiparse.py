# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2009 Fraunhofer-Institut fuer Experimentelles
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
import re
import urllib

from elementtree import ElementTree as et

from relrdf.expression.uri import Uri, Namespace
from relrdf.expression.literal import Literal
from relrdf.basesinks import PrintSink
from relrdf import commonns


# Default namespace for generated RDF model instances.
defaultInstNs = Namespace('http://example.com/model.xmi#')

class XmiParser(object):
    """Basic parser for XMI encoded models.
    """

    __slots__ = ('instNs',)

    def __init__(self, instNs=defaultInstNs):
        self.instNs = instNs

    nsMap = { u'org.omg.xmi.namespace.UML':
              Namespace('urn:org.omg.xmi.namespace.UML.') }
    defaultNs = Namespace('urn:org.omg.xmi.namespace.')

    _tagPtr = re.compile(r'({([^}]+)})?(.*)')

    @classmethod
    def uriFromTag(cls, tag):
        m = cls._tagPtr.match(tag)
        ns = cls.nsMap.get(m.group(2), cls.defaultNs)
        return ns[m.group(3)]

    def parse(self, source, sink):
        # The current entity is the entity whose definition we are now
        # seeing. Since entity definitions are nested, we use a stack
        # to put entities on hold while their nested entities are
        # processed.
        curEntity = None
        entityStack = []

        # The current parent-element-nested-element relation. The
        # relation stack works like the entity stack.
        curRel = None
        relStack = []

        for event, elem in et.iterparse(source, events=('start', 'end')):
            if event == 'start':
                xmiId = elem.get('xmi.id')
                if xmiId is not None:
                    entityUri = self.instNs['id' +
                                            urllib.quote(elem.get('xmi.id'),
                                                         safe='')]

                    if curRel is not None:
                        # Create a conection from the parent entity to
                        # this entity.
                        sink.triple(curEntity, curRel, entityUri)

                    # We have a new current entity.
                    entityStack.append(curEntity)
                    curEntity = entityUri

                    # Declare the entity type.
                    sink.triple(entityUri, commonns.rdf.type,
                                self.uriFromTag(elem.tag))

                    # Create one statement for each entity attribute.
                    for name, value in elem.items():
                        if name == 'xmi.id':
                            continue
                        sink.triple(entityUri, self.uriFromTag(name),
                                    Literal(value))
                elif curEntity is not None:
                    # This element denotes the relation between the parent
                    # element and its subelements.
                    relStack.append(curRel)
                    curRel = self.uriFromTag(elem.tag)
            else:
                if elem.get('xmi.id') is not None:
                    curEntity = entityStack.pop()
                elif curEntity is not None:
                    curRel = relStack.pop()

        assert curEntity is None
        assert curRel is None
