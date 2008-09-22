
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

