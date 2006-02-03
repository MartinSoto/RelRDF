import sys

import RDF

TYPE_RESOURCE = '<RESOURCE>'
TYPE_BLANK = '<BLANKNODE>'
TYPE_LITERAL = '<LITERAL>'
    
class PrintSink(object):
    def triple(self, subject, pred, objectType, object):
        print subject.encode('utf8'), pred.encode('utf8'), \
              objectType.encode('utf8'), object.encode('utf8')
        pass

def parseURI(uri, base=None, sink=None):
    if sink == None:
        sink = PrintSink()

    parser = RDF.RDFXMLParser()
    for stmt in parser.parse_as_stream(uri, base_uri=base):
        if stmt.object.is_resource():
            objectType = TYPE_RESOURCE
            object = stmt.object.uri
        elif stmt.object.is_blank():
            objectType = TYPE_BLANK
            object = stmt.object.blank_identifier
        else:
            object = stmt.object.literal_value['string']
            objectType = stmt.object.literal_value['datatype']
            if objectType == None:
                objectType = TYPE_LITERAL

        sink.triple(unicode(stmt.subject.uri), unicode(stmt.predicate.uri),
                    unicode(objectType), unicode(object))

if __name__ == "__main__": 
    parseURI(sys.argv[1], sink=PrintSink())
