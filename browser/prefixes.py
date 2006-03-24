namespaces = {
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'vmxt': 'http://www.v-modell.iabg.de/Schema#',
    'inst': 'http://www.kbst.bund.de/V-Modell-XT.xml#',

    'modale': 'http://www.modale.de/Beispiel#',
    'kuka': 'http://www.kuka.de/Modale#'}


def shortenUri(uri):
    text = str(uri)
    for (abbrev, nsUri) in namespaces.items():
        if text[:len(nsUri)] == nsUri:
            return abbrev + ":" + text[len(nsUri):]

    return '<%s>' % text

