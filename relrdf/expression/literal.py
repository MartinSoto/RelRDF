from relrdf.commonns import xsd


class Literal(object):
    __slots__ = ('value',
                 'typeUri',
                 'lang')

    def __init__(self, value, lang=None, typeUri=None):
        self.value = value

        if lang is not None:
            self.lang = lang
            self.typeUri = None
        elif typeUri is not None:
            self.lang = None
            self.typeUri = typeUri
        else:
            self.lang = None
            # Try to determine an appropriate type URI.
            if value is False or value is True:
                self.typeUri = xsd.boolean
            elif isinstance(value, int) or isinstance(value, long):
                self.typeUri = xsd.decimal
            elif isinstance(value, float):
                self.typeUri = xsd.double
            else:
                self.typeUri = None

    def toXsd(self):
        """Return the literal's value in standard XSD representation."""
        # FIXME: Check that this is correct in all practical cases.
        return str(self.value)

    def getCanonical(self):
        """Return the canonical string representation of the literal."""
        if self.typeUri == None and self.lang == None:
            return '"%s"' % self
        elif self.typeUri != None:
            return '"%s"^^<%s>' % (self, self.typeUri)
        else:
            return '"%s"@%s' % (self, self.lang)

    def __str__(self):
        return str(self.value)

    def __unicode__(self):
        return unicode(self.value)
