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
