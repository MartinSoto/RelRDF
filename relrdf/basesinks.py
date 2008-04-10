from relrdf.expression import uri, blanknode, literal
from relrdf.commonns import rdf


class NullSink(object):
    """An RDF sink that ignores triples passed to it."""

    __slots__ = ()

    def triple(self, subject, pred, object):
        pass

    def close(self):
        pass


class PrintSink(object):
    """An RDF sink that prints triples passed to it."""

    def triple(self, subject, pred, object):
        if isinstance(object, uri.Uri):
            objStr = '<%s>' % object
        elif isinstance(object, blanknode.BlankNode):
            objStr = 'bnode:%s' % object
        elif isinstance(object, literal.Literal):
            objStr = '"%s"' % object
        else:
            assert False, "Unexpected object type '%s'" \
                   % object.__class__.__name__
            
        print "<%s> <%s> %s" % (subject.encode('utf8'),
                                pred.encode('utf8'), \
                                objStr.encode('utf8'))

    def close(self):
        pass

class ListSink(list):
    """An RDF sink that stores triples as a list"""
    
    def triple(self, subject, pred, object):
        self.append((subject, pred, object))

class DictSink(dict):
    """An RDF sink that stores triples as a dictionary"""
    
    def triple(self, subject, pred, object):
        self[subject, pred] = object
        
    def getList(self, base):
        
        # Search list elements
        list = []
        visited = set()
        while True:            

            # Invalid node?
            if not isinstance(base, blanknode.BlankNode):
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
