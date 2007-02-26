from relrdf.commonns import xsd


class Literal(unicode):
    __slots__ = ('typeUri',
                 'lang')

    def __new__(cls, value, lang=None, typeUri=None):
        if lang is not None:
            typeUri = None
        elif typeUri is not None:
            lang = None
        else:
            lang = None

            # Try to determine an appropriate type URI.
            if value is False or value is True:
                typeUri = xsd.boolean
            elif isinstance(value, int) or isinstance(value, long):
                typeUri = xsd.integer
            elif isinstance(value, float):
                typeUri = xsd.double
            else:
                typeUri = None

        literal = super(Literal, cls).__new__(cls, value)
        literal.lang = lang
        literal.typeUri = typeUri

        return literal

    def getValue(self):
        """Return a Python value for the literal."""
        # Check if a value conversion is necessary, and perform it.
        if self.typeUri == xsd.boolean:
            return bool(self)
        elif self.typeUri == xsd.integer:
            return int(self)
        elif self.typeUri == xsd.decimal or self.typeUri == xsd.double:
            return float(self)
        else:
            return self

    value = property(getValue)

    def toXsd(self):
        """Return the literal's value in standard XSD representation."""
        return self

    def getCanonical(self):
        """Return the canonical string representation of the literal."""
        if self.typeUri == None and self.lang == None:
            return '"%s"' % self
        elif self.typeUri != None:
            return '"%s"^^<%s>' % (self, self.typeUri)
        else:
            return '"%s"@%s' % (self, self.lang)
