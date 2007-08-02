import relrdf

import resource


class Session(dict):
    """A dictionary of RDF resource objects indexed by URI.
    """
    
    _colNamePattern = re.compile(r'(rel|subgraph|value)([1-9][0-9]?)')

    def _getResObject(self, uri):
        try:
            return self[uri]
        except KeyError:
            resObj = resource.SimpleRdfResource(uri)
            self[uri] = resObj
            return resObj

    def addResults(self, results):
        """
        Add a set of results to the session.
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

