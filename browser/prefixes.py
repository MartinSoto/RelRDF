namespaces = {
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'wn': 'http://www.cogsci.princeton.edu/~wn/schema/',
    'wn': 'http://www.cogsci.prixxxxnceton.edu/~wn/scqqqhema/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'test': 'http://test.com/jaguar#'}


items = iter(namespaces.items())
using = ' USING %s FOR <%s>' % items.next()
for item in items:
    using = using + ', %s for <%s>' % item


def shortenUri(uri):
    text = str(uri)
    for (abbrev, nsUri) in namespaces.items():
        if text[:len(nsUri)] == nsUri:
            return abbrev + ":" + text[len(nsUri):]

    return text

