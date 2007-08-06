import relrdf

from resource import RdfResource, SimpleRdfResource
from resultfilter import stmtsFromResults


class Session(dict):
    """A dictionary of RDF resource objects indexed by URI.
    """
    
    def _getResObject(self, uri):
        try:
            return self[uri]
        except KeyError:
            resObj = SimpleRdfResource(uri)
            self[uri] = resObj
            return resObj

    def addResults(self, results):
        """
        Add a results object to the session.
        """
        for resUri, rel, value, subgraph in stmtsFromResults(results):
            if isinstance(value, relrdf.Uri):
                value = self._getResObject(value)

            res = self._getResObject(resUri)
            res.og.addValue(rel, value, subgraph)
            if isinstance(value, RdfResource):
                value.ic.addValue(rel, res, subgraph)
