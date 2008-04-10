
from uuid import uuid4

class BlankNode(unicode):
    """A low level representation of an RDF blank node."""
    pass

def newBlankNode():
    return BlankNode("bnode:" + unicode(uuid4()))
