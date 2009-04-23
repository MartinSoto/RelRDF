# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2009 Fraunhofer-Institut fuer Experimentelles
#                         Software Engineering (IESE).
#
# RelRDF is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA. 


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
            if isinstance(value, bool):
                typeUri = xsd.boolean

                # Normalize the value to the canonical XSD representation.
                if value:
                    value = 'true'
                else:
                    value = 'false'
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
            return self == 'true'
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
