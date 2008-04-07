
from relrdf.expression import uri, blanknode, literal

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
                blanks[node] = blanknode.BlankNode()
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
            
        
