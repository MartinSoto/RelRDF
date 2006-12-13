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


class Extender(ResultTransformer):
    __slots__ = ('functions',
                 'fixed',
                 'posMap',
                 'currentResult')

    def __init__(self, origResults, **newCols):
        self.posMap = {}
        for i, name in enumerate(origResults.columnNames):
            self.posMap[name] = i

        funcNames = []
        self.functions = []
        fixedNames = []
        self.fixed = []
        for colName, value in newCols.items():
            if hasattr(value, '__call__'):
                funcNames.append(colName)
                self.functions.append(value)
            else:
                fixedNames.append(colName)
                self.fixed.append(unicode(value))

        columnNames = list(origResults.columnNames)
        columnNames.extend(fixedNames)
        columnNames.extend(funcNames)

        super(Extender,
              self).__init__(origResults, columnNames=columnNames)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.currentResult[key]
        else:
            return self.currentResult[self.posMap[key]]

    def transformResult(self, result):
        newResult = list(result)

        newResult.extend(self.fixed)

        self.currentResult = result
        newResult.extend((func(self)
                          for func in self.functions))

        return newResult

