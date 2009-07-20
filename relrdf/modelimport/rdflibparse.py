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


from relrdf.expression import uri,  literal

import rdflib
from rdflib.Graph import Graph
from rdflib.Literal import Literal
from rdflib.URIRef import URIRef
from rdflib.BNode import BNode

class RdfLibParser(object):
    """Wrapper for rdflib RDF parser
    """

    __slots__ = ('format', )

    def __init__(self, format="nt"):
        self.format = format

    def _transValue(self, node, blanks):
        if isinstance(node, Literal):
            return literal.Literal(node, node.language, node.datatype)
        elif isinstance(node, URIRef):
            return uri.Uri(node)
        elif isinstance(node, BNode):
            try:
                return blanks[node]
            except KeyError:
                blanks[node] = uri.newBlank()
                return blanks[node]
        else:
            assert False, "Received unknown node type from rdflib: " + node.__class__.__name__

    def parse(self, source, sink):

        # Create parser
        graph = Graph()
        graph.parse(source, format=self.format)

        # Insert values into sink
        blanks = {}
        for stmt in graph:
            sink.triple(self._transValue(stmt[0], blanks),
                        self._transValue(stmt[1], blanks),
                        self._transValue(stmt[2], blanks))

