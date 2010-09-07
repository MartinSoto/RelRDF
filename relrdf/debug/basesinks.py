# -*- coding: utf-8 -*-
# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (C) 2005-2009, Fraunhofer Institut Experimentelles
#                          Software Engineering (IESE).
# Copyright (C) 2010,      Martín Soto
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


from relrdf.localization import _
from relrdf.error import InstantiationError
from relrdf.expression import uri, literal
from relrdf.modelbase import Modelbase, Sink
from relrdf.commonns import rdf

import config


class NullSink(Sink):
    """An RDF sink that ignores triples passed to it."""

    __slots__ = ()

    def triple(self, subject, pred, object):
        pass


class PrintSink(Sink):
    """An RDF sink that prints triples passed to it."""

    def triple(self, subject, pred, object):
        if isinstance(object, uri.Uri):
            objStr = '<%s>' % object
        elif isinstance(object, literal.Literal):
            objStr = '"%s"' % object
        else:
            assert False, "Unexpected object type '%s'" \
                   % object.__class__.__name__

        print "<%s> <%s> %s" % (subject.encode('utf8'),
                                pred.encode('utf8'), \
                                objStr.encode('utf8'))


class ListSink(Sink, list):
    """An RDF sink that stores triples as a list"""

    def triple(self, subject, pred, object):
        self.append((subject, pred, object))


class DictSink(Sink, dict):
    """An RDF sink that stores triples as a dictionary"""

    def triple(self, subject, pred, object):
        self[subject, pred] = object

    def getList(self, base):

        # Search list elements
        list = []
        visited = set()
        while True:

            # Invalid node?
            if not isinstance(base, uri.Uri) or not base.isBlank():
                return list

            # Check for loop
            assert not base in visited
            visited.add(base)

            # Search list element
            try:
                first = self[base, rdf.first]
                rest = self[base, rdf.rest]
            except KeyError:
                return list

            # Add, continue with next element
            list.append(first)
            base = rest

class DebugModelbase(Modelbase):
    """An incomplete modelbase used to instantiate and serve the
    debugging sinks in this module."""

    __slots__ = ()

    name = 'debug'

    def __init__(self, **kwArgs):
        # Ignore the arguments.
        pass

    def getSink(self, modelConf):
        assert isinstance(modelConf, config.DebugModelConfiguration)

        if modelConf.name == 'null':
            return NullSink(**modelConf.getParams())
        elif modelConf.name == 'print':
            return PrintSink(**modelConf.getParams())
        elif modelConf.name == 'list':
            return ListSink(**modelConf.getParams())
        elif modelConf.name == 'dict':
            return DictSink(**modelConf.getParams())
        else:
            assert False, "Unidentified model configuration"


def getModelbase(mbConf):
    assert isinstance(mbConf, config.DebugConfiguration)
    return DebugModelbase(**mbConf.getParams())
