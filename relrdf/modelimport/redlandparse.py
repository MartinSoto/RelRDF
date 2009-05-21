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

import RDF

class RedlandParser(object):
    """Wrapper for Redland RDF parser library
    """

    __slots__ = ('format', )

    def __init__(self, format="turtle"):
        self.format = format
        
    def _transValue(self, node, blanks):
        if node.is_literal():
            datatype = node.literal_value['datatype']
            if not datatype is None:
                datatype = str(datatype)
            return literal.Literal(node.literal_value['string'],
                                   node.literal_value['language'],
                                   datatype)
        elif node.is_resource():
            return uri.Uri(node.uri)
        elif node.is_blank():
            try:
                return blanks[node.blank_identifier]
            except KeyError:
                blanks[node.blank_identifier] = uri.newBlank()
                return blanks[node.blank_identifier]
        else:
            assert False, "Received unknown node type from RedLand RDF parser"

    def parse(self, source, sink):
 

        # Make valid source URI
        source = str(source)
        if source.find("://") < 0:
            source = "file://" + source
        
        # Create parser
        parser = RDF.Parser(name=self.format)
        stream = parser.parse_as_stream(str(source))

        # Insert values into sink
        blanks = {}
        for stmt in stream:
            sink.triple(self._transValue(stmt.subject, blanks), 
                        self._transValue(stmt.predicate, blanks),
                        self._transValue(stmt.object, blanks))

