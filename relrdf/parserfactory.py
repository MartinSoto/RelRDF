import serql

def getQueryParser(queryLanguage, **parserArgs):
    queryLanguageNorm = queryLanguage.lower()
    if queryLanguageNorm == 'serql':
        try:
            prefixes = parserArgs['prefixes']
        except KeyError:
            prefixes = {}
        return serql.Parser(prefixes)
    else:
        assert False, "invalid query language '%s'" % queryLanguage


