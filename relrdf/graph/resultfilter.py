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
