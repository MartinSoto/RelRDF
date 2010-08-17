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

"""
Transformation of query results.
"""

__docformat__ = "restructuredtext en"


from relrdf import commonns
from relrdf.expression import uri
from relrdf.util import nsshortener


class ResultTransformer(object):
    """A generic class for performing arbitrary transformations on a
    query results stream."""

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

    def __iter__(self):
        for result in self.origResults:
            yield self.transformResult(result)


class ShortenUris(ResultTransformer):
    """A result transformer that shortens all URIs present a result."""

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


class PropMap(object):
    """A property map for transformation operations.

    An object of this class is passed to every tranformation functions
    applyed by a `PropertyTransformer` object whenever they are
    called. It is a wrapper around a result object, which uses the
    position map passed at initialization to access particular
    positions in the result.
    """

    __slots__ = ('opPosMap',
                 'currentResult',
                 )

    def __init__(self, opPosMap):
        self.opPosMap = opPosMap

        # The current result is transient and will be set
        # externally every time a result is transformed with this
        # object.
        self.currentResult = None

    def __getitem__(self, key):
        return self.currentResult[self.opPosMap[key]]

    def __setitem__(self, key, value):
        self.currentResult[self.opPosMap[key]] = value


class PropertyTransformer(ResultTransformer):
    """Transform query results based on arbitrary transformation
    functions.

    For the graph generation system, results specify properties for
    potentially three graph elements: the first (starting) node of an
    edge, the last (ending) node of an edge, and the edge (connecting
    arrow) itself. A so-called *transformation function* is a Python
    callable object that, when called, is expected to transform one or
    more properties of one such graph element into one or more
    properties for the same graph element. Transformation functions
    can thus be used to, for example, calculate graphical properties
    for a graph element, based on other more abstract properties
    already present in a result, or to calculate the values of certain
    unspecified graphical properties based on the values of the
    specified ones.

    A `PropertyTransformer` object receives a sequence of
    transformation functions and tries to apply them to each one of
    the graph elements mentioned by the transformed results. In order
    to apply a transformation function to a certain graph element, all
    input properties of the function must be already present in the
    result for that particular element. If the outputProperties of the
    function are not yet present in the result, the result will be
    extended to add them to it.
    """

    __slots__ = ('funcsToRun',
                 'propMap',
                 )


    def __init__(self, origResults, transfFuncs):
        """Create a new `PropertyTransformer`.

        :Parameters:

          - `origResults`: The original results object.

          - `transfFuncs`: Specifies the transformation functions to
            apply to processed graph elements. It is an iterable
            containing tuples of the form ``(inputProps, outputProps,
            func)``, where:
            
            - ``inputProps`` is an iterable containing the names of
              the input properties of the function in generic form
              (i.e., ``'color'`` instead of ``'color1'`` or
              ``'edge_color'``.)

            - ``outputProps`` is an iterable containing the names of
              the output properties of the function in generic form.

            - ``func`` is the actual transformation function (a
              callable object). For every processed graph element,
              this function will be called with a single property map
              ``m`` as parameter. The function is allowed to consult
              properties as ``m['prop-name']`` and to write to
              properties by assigning to ``m['prop-name']``. No other
              operators or methods should be used on on the property
              map.

            Functions will be applied to every graph element in
            iteration order.
        """

        # Since the column names are known from the beginning, it is
        # possible to determine in advance which transformation
        # functions apply to which entities:

        # Initially, the extended column names are the same of the
        # original results object.
        columnNames = list(origResults.columnNames)
    
        # A dictionary that maps result column names to result
        # positions.
        posMap = {}
        for i, name in enumerate(columnNames):
            posMap[name] = i

        # The list of transformation operations to run on every
        # result. It consists of tuples of the form `(func, propMap)`
        # where `func` is a transformation function and `propMap` is
        # the `self.PropMap` instance to give to the function.
        self.funcsToRun = []

        for inputProps, outputProps, func in transfFuncs:
            # The formats correspond to the three graph entities
            # potentially mentioned by a result: the first node, the
            # second node, and the edge.
            for fmt in ('%s1', '%s2', 'edge_%s'):
                # In order for the operation to apply to a particular
                # entity, the result must include all input properties
                # for that entity.
                applies = True
                for inputProp in inputProps:
                    if not fmt % inputProp in posMap:
                        applies = False
                        break
                if not applies:
                    continue

                # Build a dictionary that maps the operation's input
                # and output property names to result positions.
                opPosMap = {}
                for inputProp in inputProps:
                    opPosMap[inputProp] = posMap[fmt % inputProp]
                for outputProp in outputProps:
                    columnName = fmt % outputProp
                    try:
                        opPosMap[outputProp] = posMap[columnName]
                    except KeyError:
                        # Results must be extended to hold this output
                        # column.
                        columnNames.append(columnName)
                        posMap[columnName] = len(columnNames) - 1
                        opPosMap[outputProp] = len(columnNames) - 1

                self.funcsToRun.append((func, PropMap(opPosMap)))

        super(PropertyTransformer, self).__init__(origResults,
                                                  columnNames=columnNames)

    def __iter__(self):
        # The number of columns to add to every result.
        extendCount = len(self.columnNames) - \
                      len(self.origResults.columnNames)

        for result in self.origResults:
            # Copy the result and extend it to its final size.
            newResult = list(result)
            newResult.extend([None] * extendCount)

            for func, propMap in self.funcsToRun:
                # Put the result in the map.
                propMap.currentResult = newResult

                # Invoke the function on the map.
                func(propMap)

            yield newResult


def transf(inputProps, outputProps):
    """A decorator to define property transformation functions.

    The decorator can precede the definition of a transformation
    function as ``@transf(inputProps, outputProps)`` where:

    :Parameters:

      - `inputProps`: is an iterable containing the names of the
        function's input properties.

      - `outputProps`: is an iterable containing the names of the
        function's output properties.

    :Return: A tuple suitable for use when creating a
      `PropertyTransformer`.
    """

    return lambda(func) : (inputProps, outputProps, func)
