# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2010 Fraunhofer-Institut fuer Experimentelles
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

"""A customized namespace shortener implementation for ModelWorkshop.

This implementation uses the ModelWorkshop conventions for embedding
URIs in other URIs.
"""

from relrdf import commonns as ns
from relrdf.util.nsshortener import NamespaceUriShortener

from iriprotect import protectIri


class MWUriShortener(NamespaceUriShortener):
    __slots__ = ()

    def __init__(self, **kwargs):
        super(MWUriShortener, self).__init__(shortFmt='%s_%s',
                                             longFmt='uri_%s',
                                             **kwargs)

    def shortenUri(self, uri):
        shortened = super(MWUriShortener, self).shortenUri(uri)
        return protectIri(shortened)


_cache = {}

def getPrefixes(model):
    """Get a shortener for the given model."""
    try:
        return _cache[model]
    except KeyError:
        shortener = MWUriShortener()

        shortener.addPrefix('rdf', ns.rdf)
        shortener.addPrefix('rdfs', ns.rdfs)
        shortener.addPrefix('relrdf', ns.relrdf)

        # Add the namespaces from the model.
        shortener.addPrefixes(model.getPrefixes())

        _cache[model] = shortener

        return shortener
