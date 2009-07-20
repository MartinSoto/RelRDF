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


import re

import relrdf


_colNamePattern = re.compile(r'(rel|subgraph|value)([1-9][0-9]?)')

def stmtsFromResults(results):
    """
    Produce a set of statements from a results object.

    A column naming convention is used to determine the meaning of the
    result columns.
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
        m = _colNamePattern.match(colName)
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

    # Iterate over the results generating statements.
    for result in results:
        for resNumber, relCol in relCols.items():
            rel = result[relCol]
            if not isinstance(rel, relrdf.Uri):
                continue

            try:
                resCol = valueCols[resNumber]
                valueCol = valueCols[resNumber + 1]
            except KeyError:
                continue

            resUri = result[resCol]
            if not isinstance(resUri, relrdf.Uri):
                continue

            value = result[valueCol]
            if value is None:
                continue
            elif isinstance(value, relrdf.Literal):
                # Take the raw literal value.
                value = value.value

            if resNumber in subgraphCols:
                subgraph = result[subgraphCols[resNumber]]
                if not isinstance(subgraph, relrdf.Uri):
                    subgraph = None
            else:
                subgraph = None

            yield (resUri, rel, value, subgraph)
