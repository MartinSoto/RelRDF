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

"""Classes and functions related to the in-memory representation of
RDF resources.
"""

import re
import itertools

from relrdf.expression import uri, literal


class RdfResourceSide(object):
    """A 'side' of an RDF resource.

    An RDF resource can be seen as having two 'sides': one formed by
    all relations going out from the resource (i.e., having the
    resource as subject) together with their target
    resources/literals, and one formed by all relations coming into
    the resource (i.e., having the resource as object) together with
    the resources where they originate.

    This interface represents one such resource side.
    """

    __slots__ = ()


    def rels(self):
        """Iterate over this side's relations.

        :Returns: An iterable over this resource side's relation URIs,
        in no particular order."""
        return NotImplemented

    def hasRel(self, rel):
        """Determine if this side as a value for a given relation.

        :Parameters:

        - `rel`: A relation URI.

        :Returns: True if `rel` is in the side, false otherwise.
        """
        return NotImplemented

    def values(self, rel):
        """Iterate over the literals/resources associated to a relation.

        :Parameters:

        - `rel`: A relation URI.

        :Returns: An iterable over the resources/literals associated
        to relation `rel` in this resource side, in no particular
        order. Literals are returned as Python values. Resources are
        returned as `RdfResource` objects.
        """
        return NotImplemented

    def value(self, rel, default=None):
        """Get one value for a relation.

        :Parameters:

        - `rel`: A relation URI.
        
        - `default`: A default value to return if the relation is not
          found.

        :Returns: One of the values for relation `rel` in this
        resource side (if more than one value is available, the choice
        is arbitrary) or the value of `default` if no value is
        present.
        """
        try:
            return iter(self.values(rel)).next()
        except KeyError:
            return default

    def valueFromFirst(self, rels, default=None):
        """Get one value for one relation from a sequence.

        This method takes a sequence of relations and tests them in
        order until it finds one that has values for this resource. It
        then returns one of those values.

        :Parameters:

        - `rels`: An iterable of relations.
        
        - `default`: A default value to return if the none of the
          relations has values..

        :Returns: One of the values (the choice is arbitrary) for the
        first relation in `rels` having values, or `None` if none of
        the relations in `rels` has values for this resource.
        """
        for rel in rels:
            value = self.value(rel)
            if value is not None:
                return value
        return default

    def valueSubgraph(self, rel):
        """Iterate over the literals/resources associated to a relation,
        and their corresponding subgraphs.

        :Parameters:

        - `rel`: A relation URI.

        :Returns: An iterable over a sequence of pairs of the form
        ``(value, subgraph)``, where ``value`` is the relation value
        like in the `values` method, and ``subgraph`` is the subgraph
        URI of the subgraph containing the corresponding RDF
        triple. Observe that since many subgraphs may contain the
        same triple, this method may return more results than the
        `values` method for the same relation.
        """
        return NotImplemented


class RdfResource(object):
    """A memory representation of an RDF resource.

    Instances of this class can (and very often will) only contain
    partial information about their corresponding RDF resources. On
    the one hand, not all relations and values for a particular
    resource may be available to the application. On the the other
    hand, the application may decide not to load all information
    available about a resource, but only those information items
    necessary for a particular purpose.
    """

    __slots__ = ()

    @property
    def uri(self):
        """The URI identifying this resource."""

    @property
    def og(self):
        """The outgoing side of the resource"""
        return NotImplemented

    @property
    def ic(self):
        """The incoming side of the resource."""
        return NotImplemented



class SimpleResourceSide(RdfResourceSide, dict):
    """A simple implementation of an RDF resource side."""

    __slots__ = ()

    def rels(self):
        return self.keys()

    def hasRel(self, rel):
        return rel in self

    def values(self, rel):
        for value, subgraph in self[rel]:
            yield value

    def valueSubgraph(self, rel):
        return iter(self[rel])

    def addValue(self, rel, value, subgraph=None):
        """Add value `value` for relation `rel` to this resource
        side.

        :Parameters:

        - `rel`: A relation URI.

        - `value`: The simple Python value or `RdfResource` instance.

        - `subgraph`: The RDF subgraph where the
          resource-relation-value association was made. May be `None`
          if this information is not available or irrelevant.
        """
        try:
            valSub = self[rel]
        except KeyError:
            valSub = set()
            self[rel] = valSub

        valSub.add((value, subgraph))


class SimpleRdfResource(RdfResource):
    """A simple implementation of an RDF resource."""

    __slots__ = ('_uri', '_og', '_ic')


    def __init__(self, uri):
        self._uri = uri
        self._og = SimpleResourceSide()
        self._ic = SimpleResourceSide()

    def __hash__(self):
        return hash(self._uri)

    def __eq__(self, other):
        return isinstance(other, RdfResource) and self._uri == other.uri

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def uri(self):
        return self._uri

    @property
    def og(self):
        return self._og

    @property
    def ic(self):
        return self._ic



class ResourceSet(dict):
    """A dictionary of RDF resource objects indexed by URI.
    """
    
    _colNamePattern = re.compile(r'(rel|subgraph|value)([1-9][0-9]?)')

    def _getResObject(self, uri):
        try:
            return self[uri]
        except KeyError:
            resObj = SimpleRdfResource(uri)
            self[uri] = resObj
            return resObj

    def addResults(self, results):
        """
        """
        # Create data structures containing the indexes of the value
        # and relation columns. Resource numbers can go up to 99.

        # valueCols[i] contains the column index of the column
        # specifying value<i>.
        valueCols = {}

        # relCols[i] contains the column index of the column
        # specifying rel<i>'s uri.
        relCols = {}

        # subgraphCols[i] contains the column index of the column
        # specifying rel<i>'s subgraph uri.
        subgraphCols = {}

        # Fill the data structures using the column names.
        for i, colName in enumerate(results.columnNames):
            m = self._colNamePattern.match(colName)
            if m is not None:
                (colType, resNumberStr) = m.groups()
                resNumber = int(resNumberStr)

                if colType == 'rel':
                    relCols[resNumber] = i
                elif colType == 'subgraph':
                    subgraphCols[resNumber] = i
                else:
                    valueCols[resNumber] = i

        if len(valueCols) == 0 or len(relCols) == 0:
            # No work to do.
            return

        # Iterate over the results creating resource objects.
        for result in results:
            for resNumber, relCol in relCols.items():
                rel = result[relCol]
                if not isinstance(rel, uri.Uri):
                    continue

                try:
                    resCol = valueCols[resNumber]
                    valueCol = valueCols[resNumber + 1]
                except KeyError:
                    continue

                resUri = result[resCol]
                if not isinstance(resUri, uri.Uri):
                    continue

                value = result[valueCol]
                if value is None:
                    continue
                elif isinstance(value, uri.Uri):
                    value = self._getResObject(value)
                elif isinstance(value, literal.Literal):
                    # Take the raw literal value.
                    value = value.value

                # It is important to do this after we know we have a
                # value. Otherwise we may create spurious objects.
                res = self._getResObject(resUri)

                if resNumber in subgraphCols:
                    subgraph = result[subgraphCols[resNumber]]
                    if not isinstance(subgraph, uri.Uri):
                        subgraph = None
                else:
                    subgraph = None

                res.og.addValue(rel, value, subgraph)
                if isinstance(value, RdfResource):
                    value.ic.addValue(rel, res, subgraph)

