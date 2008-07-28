from relrdf.localization import _
from relrdf.error import InstantiationError
from relrdf.expression import uri, blanknode, literal


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


class DebugModelBase(object):
    """An incomplete model base to instantiate and serve the debugging
    sinks in this class."""

    __slots__ = ()

    def getSink(self, sinkType, **sinkArgs):
        sinkTypeNorm = sinkType.lower()

        try:
            if sinkTypeNorm == 'null':
                return NullSink(**sinkArgs)
            elif sinkTypeNorm == 'print':
                return PrintSink(**sinkArgs)
            else:
                raise InstantiationError(_("Invalid sink type '%s'") % sinkType)
        except TypeError, e:
            raise InstantiationError(_("Missing or invalid sink arguments: %s")
                                     % e)

    def close(self):
        pass

def getModelBase(**modelBaseArgs):
    return DebugModelBase(**modelBaseArgs)
