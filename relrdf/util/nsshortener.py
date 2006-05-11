from relrdf import commonns

class NamespaceUriShortener(object):
    """Convert URIs into a shortened form using a set of namespace prefixes.

    This class maintains a set of namespace prefixes with their
    corresponding namespace URIs. Method `shortenUri` converts URIs
    (when possible) to their shortened form, using the prefixes in the
    set."""

    __slots__ = ('nsDict',
                 'shortFmt',
                 'longFmt')

    def __init__(self, shortFmt, longFmt):
        self.nsDict = {}
        self.shortFmt = shortFmt
        self.longFmt = longFmt

    def addPrefix(self, prefix, nsUri):
        """Add the prefix `prefix` to the internal set with namespace
        URI `nsUri`.

        This method clobbers any existing definition for the same prefix."""
        self.nsDict[prefix] = nsUri

    def addPrefixes(self, dict):
        """Add the prefixes in `dict` to the internal prefix set.

        `dict` is a dictionary with prefixes as keys and namespace URIs
        as values. Existing prefixes in the internal set get clobbered
        by new definitions in `dict`."""
        for prefix, nsUri in dict.items():
            self.nsDict[prefix] = nsUri
    
    def shortenUri(self, uri):
        """Attempt to shorten a URI using the prefixes in the internal set.

        If a matching namespace is found, the prefix and the remaining
        part of the URI will be passed to the `shortFmt` format of
        this object to form a string. Otherwise the `longFmt` format
        of this object will be used."""
        
        text = unicode(uri)
        for (prefix, nsUri) in self.nsDict.items():
            if text.startswith(nsUri):
                # FIXME: Check that the remaining suffix is a valid
                # XML element name.
                return self.shortFmt % (prefix, text[len(nsUri):])

        return self.longFmt % text
