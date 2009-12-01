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


from relrdf.localization import _
from relrdf.util import nsshortener

from parsequerybase import BaseTemplate, BaseQuery


def makeTemplate(queryLanguage, queryText):
    """A factory for query templates."""

    # Import the specific template class.
    queryLanguageNorm = queryLanguage.lower()
    if queryLanguageNorm == 'sparql':
        from sparql import Template
    else:
        assert False, _("invalid query language '%s'") % queryLanguage

    assert issubclass(Template, BaseTemplate)

    return Template(queryText)

def _getQueryClass(queryLanguage):
    # Import the specific query class.
    queryLanguageNorm = queryLanguage.lower()
    if queryLanguageNorm == 'sparql':
        from sparql import Query
    else:
        assert False, _("invalid query language '%s'") % queryLanguage

    assert issubclass(Query, BaseQuery)

    return Query

def parseQuery(queryLanguageOrTemplate, queryText=None,
               fileName=_("<unknown>"),
               prefixes=nsshortener.NamespaceUriShortener(),
               model=None, **queryArgs):
    """Parse a query and return a query object.

    The returned object is an instance of ``parsequerybase.Query``."""

    if isinstance(queryLanguageOrTemplate, BaseTemplate):
        # We were called with a template.
        template = queryLanguageOrTemplate
        assert queryText is None

        # Expand the template.
        queryLanguage = template.queryLanguage
        queryText = template.substitute(queryArgs)
    elif isinstance(queryLanguageOrTemplate, basestring):
        queryLanguage = queryLanguageOrTemplate
    else:
        raise TypeError, \
            _("Invalid object type '%s' passed to parseQuery") % \
            type(queryLanguageOrTemplate).__name__

    if model is not None:
        # Add the prefixes from the model base to the set of prefixes
        # passed to this query.
        mergedPrefixes = nsshortener.NamespaceUriShortener()
        mergedPrefixes.addPrefixes(prefixes)
        mergedPrefixes.addPrefixes(model.getPrefixes())
        prefixes = mergedPrefixes

    # Make a query object and return it.
    Query = _getQueryClass(queryLanguage)
    return Query(queryText, fileName=fileName, prefixes=prefixes,
                 model=model, **queryArgs)
