import serql, sparql

def getQueryParser(queryLanguage, **parserArgs):
    try:
        prefixes = parserArgs['prefixes']
    except KeyError:
        prefixes = {}

    queryLanguageNorm = queryLanguage.lower()
    if queryLanguageNorm == 'serql':
        return serql.Parser(prefixes)
    elif queryLanguageNorm == 'sparql':
        return sparql.Parser(prefixes)
    else:
        assert False, "invalid query language '%s'" % queryLanguage


