import sys

import RDF

from relrdf.expression import uri, blanknode, literal
from relrdf.basesinks import PrintSink


def parseFromUri(uriRef, base=None, sink=None):
    if sink == None:
        sink = PrintSink()

    parser = RDF.RDFXMLParser()
    for stmt in parser.parse_as_stream(uriRef, base_uri=base):
        if stmt.object.is_resource():
            object = uri.Uri(stmt.object.uri)
        elif stmt.object.is_blank():
            object = blanknode.BlankNode(stmt.object.blank_identifier)
        else:
            object = literal.Literal(stmt.object.literal_value['string'],
                                     typeUri=stmt.object. \
                                     literal_value['datatype'],
                                     lang=stmt.object. \
                                     literal_value['language'])

        sink.triple(uri.Uri(stmt.subject.uri), uri.Uri(stmt.predicate.uri),
                    object)

if __name__ == "__main__": 
    parseFromUri(sys.argv[1])
