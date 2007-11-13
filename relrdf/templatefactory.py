"""A factory for query templates."""

def makeTemplate(queryLanguage, queryText):
    # Import the template factory.
    queryLanguageNorm = queryLanguage.lower()
    if queryLanguageNorm == 'sparql':
        from relrdf.sparql import Template

    return Template(queryText)
