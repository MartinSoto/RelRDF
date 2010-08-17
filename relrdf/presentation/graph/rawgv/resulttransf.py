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

from relrdf import commonns
from relrdf.expression import uri
from relrdf.util import nsshortener


class ResultTransformer(object):
    __slots__ = ('origResults',
                 'columnNames')

    def __init__(self, origResults, columnNames=None):
        self.origResults = origResults
        if columnNames is None:
            self.columnNames = origResults.columnNames
        else:
            self.columnNames = tuple(columnNames)

    def transformResult(self, result):
        return result

    def iterAll(self):
        for result in self.origResults:
            yield self.transformResult(result)

    __iter__ = iterAll


class LabelFromOldNewName(ResultTransformer):
    __slots__ = ('posOld',
                 'posNew')

    def __init__(self, origResults):
        columnNames = list(origResults.columnNames)

        self.posOld = columnNames.index('oldName')
        self.posNew = columnNames.index('newName')

        columnNames.append('label1')

        super(LabelFromOldNewName, self).__init__(origResults,
                                                  columnNames)

    def transformResult(self, result):
        result = list(result)
        result.append("%s -> %s" % (result[self.posOld], result[self.posNew]))
        return result


class ShortenUris(ResultTransformer):
    __slots__ = ('shortener',)

    def __init__(self, origResults, model):
        super(ShortenUris, self).__init__(origResults)

        self.shortener = nsshortener.NamespaceUriShortener(shortFmt='%s:%s',
                                                           longFmt='<%s>')

        # Standard namespaces.
        self.shortener.addPrefix('rdf', commonns.rdf)
        self.shortener.addPrefix('rdfs', commonns.rdfs)
        self.shortener.addPrefix('relrdf', commonns.relrdf)

        # Add the namespaces from the model.
        self.shortener.addPrefixes(model.getPrefixes())

    def transformResult(self, result):
        shortened = []
        for field in result:
            if isinstance(field, uri.Uri):
                shortened.append(self.shortener.shortenUri(field))
            else:
                shortened.append(field)

        return shortened
