from expression import uri, blanknode, literal


class NullSink(object):
    """An RDF sink that ignores triples passed to it."""

    __slots__ = ()

    def triple(self, subject, pred, object):
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
            assert False, "Unexpected object type '%d'" \
                   % object.__class__.__name__
            
        print "<%s> <%s> %s" % (subject.encode('utf8'),
                                pred.encode('utf8'), \
                                objStr.encode('utf8'))

