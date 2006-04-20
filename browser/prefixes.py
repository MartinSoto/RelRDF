import commonns

namespaces = {
    'rdf': commonns.rdf,
    'rdfs': commonns.rdfs,

    'relrdf': commonns.relrdf,

    'vmxt': 'http://www.v-modell.iabg.de/Schema#',
    'inst': 'http://www.kbst.bund.de/V-Modell-XT.xml#',

    'modale': 'http://www.modale.de/Beispiel#',
    'rdfdiffsc': 'http://www.iese.fhg.de/RDFDiff/Schema#',
    'rdfdiffst': 'http://www.iese.fhg.de/RDFDiff/Statement#',
    'kuka': 'http://www.kuka.de/Modale#',
    'dc': 'http://www.daimlerchrysler.de/modaleBeispiel#',

    'asg': 'https://asg-platform.org/cgi-bin/twiki/viewauth/Internal/ASGDevelopmentProcess#'}


def shortenUri(uri):
    text = str(uri)
    for (abbrev, nsUri) in namespaces.items():
        if text[:len(nsUri)] == nsUri:
            return abbrev + ":" + text[len(nsUri):]

    return '<%s>' % text

