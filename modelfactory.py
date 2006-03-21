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
                 'columnNames')

    def __init__(self, connection, columnNames, queryString):
        self.cursor = connection.cursor()
        self.columnNames = columnNames
        self.cursor.execute(queryString)

    def iterAll(self):
        row = self.cursor.fetchone()
        while row is not None:
            yield row
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
        columnNames = expr.columnNames
        sqlQuery = self.mapper(expr)
        return SqlBasedResults(self.connection, columnNames, sqlQuery)


def getModel(modelType, connection, prefixes=None, **kwargs):
    modelTypeNorm = modelType.lower()
    if modelTypeNorm == 'singleversion':
        mapper = sqlmap.VersionMapper(kwargs['versionId'])
#    elif modelTypeNorm == 'multiversion':
#        mapper = map.MultiVersionMapper(kwargs['versionUri'])
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
