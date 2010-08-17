# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2010 Fraunhofer-Institut fuer Experimentelles
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

"""
Special property accesors for GooGV.

Using delegate properties:

>>> class A(object): pass
>>> class B(object):
...     x = delegateProp('deleg', 'y')
>>> a, b = A(), B()
>>> b.deleg = a
>>> b.x
Traceback (most recent call last):
  ...
AttributeError: 'A' object has no attribute 'y'
>>> a.y = 'Value'
>>> b.x
'Value'
>>> del a.y
>>> b.x
Traceback (most recent call last):
  ...
AttributeError: 'A' object has no attribute 'y'
>>> b.x = 'Another value' 
>>> b.x
'Another value'
>>> a.y
'Another value'
>>> del b.x
>>> a.y
Traceback (most recent call last):
  ...
AttributeError: 'A' object has no attribute 'y'


Using GObject enumeration properties:

>>> class A(HierarchicalAttrBase):
...   x = propPangoAlignment('x')
>>> a = A()
>>> a.x = 'left'
>>> a.x
<enum PANGO_ALIGN_LEFT of type PangoAlignment>
>>> a.x = 'Left'
>>> a.x
<enum PANGO_ALIGN_LEFT of type PangoAlignment>
>>> a.x = 'NotRight'
Traceback (most recent call last):
  ...
ValueError: String value 'NotRight' not found
>>> a.x = 1
>>> a.x
<enum PANGO_ALIGN_CENTER of type PangoAlignment>
>>> a.x = '1'
Traceback (most recent call last):
  ...
ValueError: String value '1' not found
>>> a.x = pango.ALIGN_CENTER
>>> a.x
<enum PANGO_ALIGN_CENTER of type PangoAlignment>
"""

import gtk
import pango

from hierattr import HierarchicalAttrBase, typedProp


class delegateProp(object):
    """Delegated property."""

    __slots__ = ('delegAttr', 'propName')

    def __init__(self, delegAttr, propName):
        """Creates a delegated property. Whenever this property is
        referenced, property named `propName` of attribute `delegAttr`
        of `self` will be referenced."""
        self.delegAttr = delegAttr
        self.propName = propName

    def __get__(self, obj, type=None):
        return getattr(getattr(obj, self.delegAttr), self.propName)

    def __set__(self, obj, value):
        setattr(getattr(obj, self.delegAttr), self.propName, value)

    def __delete__(self, obj):
        delattr(getattr(obj, self.delegAttr), self.propName)


def gEnumProp(propName, gEnumConstructor, stringMap):
    """Create a typed property called `propName`, that uses
    `gEnumConstructor`, a GType enumeration, as its type
    constructor. Addionally, `stringMap` should be a dictionary
    mapping (lowercase) strings to the constants in the
    enumeration. The property will also convert any string values
    corresponding to keys in this dictionary to the associated
    constant. String value comparison is case insensitive."""
    def typeConst(value):
        if isinstance(value, basestring):
            try:
                return stringMap[value.lower()]
            except KeyError:
                raise ValueError, "String value '%s' not found" % value
        else:
            return gEnumConstructor(value)

    return typedProp(propName, typeConst)


_alignmentConvTbl = {
    'left': pango.ALIGN_LEFT,
    'center': pango.ALIGN_CENTER,
    'right': pango.ALIGN_RIGHT,
    }

def propPangoAlignment(propName):
    return gEnumProp(propName, pango.Alignment, _alignmentConvTbl)


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
