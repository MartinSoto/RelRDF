import gettext
gettext.install('relrdf')

import serql
import sqlmap


def getQueryParser(queryLanguage, prefixes=None):
    queryLanguageNorm = queryLanguage.lower()
    if queryLanguageNorm == 'serql':
        return serql.Parser(prefixes)
    else:
        assert False, "invalid query language '%s'" % queryLanguage


class SqlBasedResults(object):
    """A query that gets processed by translating it to SQL."""

    __slots__ = ('cursor',
                 'columnNames',
                 'mapper')

    def __init__(self, connection, columnNames, mapper, expr):
        self.cursor = connection.cursor()

        # Make sure MySQL send us UTF8.
        self.cursor.execute('set names "utf8"')

        self.columnNames = columnNames
        self.mapper = mapper

        self.cursor.execute(mapper.mapExpr(expr))

    def iterAll(self):
        row = self.cursor.fetchone()
        while row is not None:
            result = []
            for rawValue, typeId in zip(row[0::2], row[1::2]):
                result.append(self.mapper.convertResult(rawValue, typeId))
            yield tuple(result)

            row = self.cursor.fetchone()

    __iter__ = iterAll


class SqlMappedModel(object):
    """An RDF model defined through a certain mapping from relational
    expressions to SQL."""

    __slots__ = ('connection',
                 'mapper',
                 'prefixes')

    def __init__(self, connection, mapper, prefixes=None):
        self.connection = connection
        self.mapper = mapper
        self.prefixes = prefixes

    def query(self, queryLanguage, queryText, fileName=_("<unknown>")):
        parser = getQueryParser(queryLanguage, self.prefixes)
        expr = parser.parse(queryText, fileName)
        return SqlBasedResults(self.connection,
                               list(expr.columnNames),
                               self.mapper, expr)


def getModel(modelType, connection, prefixes=None, **kwargs):
    modelTypeNorm = modelType.lower()
    if modelTypeNorm == 'singleversion':
        mapper = sqlmap.SingleVersionMapper(kwargs['versionId'])
    elif modelTypeNorm == 'allversions':
        mapper = sqlmap.AllVersionsMapper()
    elif modelTypeNorm == 'twoway':
        mapper = sqlmap.TwoWayComparisonMapper(kwargs['versionA'],
                                               kwargs['versionB'])
    else:
        assert False, "invalid model type '%s'" % modelType

    return SqlMappedModel(connection, mapper, prefixes)
 

if __name__ == '__main__':

    import sys
    import MySQLdb

    prefixes = {
        'ex': 'http://example.com/model#'
        }

    connection = MySQLdb.connect(host='localhost', db=sys.argv[1],
                                 read_default_group='client')

    kwargs = {}
    for arg in sys.argv[3:]:
        key, value = arg.split('=')
        kwargs[key] = value

    model = getModel(sys.argv[2], connection, prefixes, **kwargs)
    result = model.query('SerQL', sys.stdin)
    print result.columnNames
    for row in result.iterAll():
        print row
