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
Support for hierarchical attributes with optional default values.

This module provides a base class (`HierarchicalAttrBase`) that
changes the behavior of attributes in derived instances. Instances can
be organized in a hierarchy, where an object references its parent
using an attribute or method. When there is an attempt to consult an
attribute from one such object, its value is searched for in the
following sequence:

* If a value for the attribute is present in the object's __dict__,
  this value is returned. If not,

* if the object (or, by extension, its class) has an attribute called
  _defaults, it must be a dictionary. If it contains a key named as
  the attribute, the associated value will be returned. If not,

* if the object has a parent that is different from `None`, an attempt
  will be done to retrieve the value from it, using `getattr`. If this
  succeeds, this value will be returned. This means that when the
  parent object is also a `HierarchicalAttrBase`, the process will be
  repeated recursively.

* Otherwise, an error will occur.

These are some examples of the system in action:

>>> class A(HierarchicalAttrBase):
...     _defaults = {'x': '5'}
>>> a = A()
>>> a.y
Traceback (most recent call last):
  ...
AttributeError: 'A' object has no attribute 'y'
>>> a.x
'5'
>>> b = A()
>>> b._parent = a
>>> a.x, b.x
('5', '5')
>>> a.x = '1'
>>> a.x, b.x
('1', '5')
>>> class C(HierarchicalAttrBase): pass
>>> c=C()
>>> c._parent = a
>>> a.x, c.x
('1', '1')
>>> c.x = '3'
>>> a.x, c.x
('1', '3')
>>> del c.x
>>> c.x
'1'
>>> b.x = '3'
>>> del a.x
>>> a.x
'5'
>>> b.x
'3'


This module also offers the `typedProp` factory to create attributes
that are automatically converted into an arbitrary type as necessary.

>>> class D(HierarchicalAttrBase):
...     x = typedProp('x', int)
>>> d = D()
>>> d.x
Traceback (most recent call last):
  ...
AttributeError: 'D' object has no attribute 'x'
>>> d._parent = a
>>> d.x
5
>>> a.x = '1'
>>> a.x, d.x
('1', 1)
>>> d.x = '3'
>>> a.x, d.x
('1', 3)
>>> d.x = 4
>>> a.x, d.x
('1', 4)
>>> del d.x
>>> a.x, d.x
('1', 1)


Errors get reported using the right class:

>>> d.z
Traceback (most recent call last):
  ...
AttributeError: 'D' object has no attribute 'z'
"""


class HierarchicalAttrBase(object):
    """Base class implementing hierarchical property handling.

    Nodes of a hierarchy must derive from this base class in order for
    hierarchical attributes to work. They must also provide a
    `_parent` attribute pointing to their parent object in the
    hierarchy, or redefine the `_getParent()` method to return it. The
    values of either `_parent` or `_getParent()` must be `None` for
    the hierarchy's topmost object.
    """

    _defaults = {}

    # No parent by default.
    _parent = None

    def _getParent(self):
        return self._parent

    def __getattr__(self, name):
        """Retrieve missing attributes from the default table or from
        the parent."""
        try:
            return self._defaults[name]
        except KeyError:
            parent = self._getParent()
            if parent is None:
                raise AttributeError, \
                      "'%s' object has no attribute '%s'" % \
                      (self.__class__.__name__, name)
            else:
                try: 
                    return getattr(parent, name)
                except AttributeError:
                    raise AttributeError, \
                          "'%s' object has no attribute '%s'" % \
                          (self.__class__.__name__, name)

    def _getAttrValue(self, name):
        """Retrieve the value of attribute `name` and return it.

        If an accesor for the attribute is present in the class, this
        method bypasses it."""
        try:
            return self.__dict__[name]
        except KeyError:
            # Try the parent.
            return self.__getattr__(name)


class typedProp(object):
    """Typed property for use in `HierarchicalAttrBase` derived
    classes.

    Instances of classes using this accesor must provide a `__dict__`
    dictionary."""

    __slots__ = ('propName', 'typeFactory')

    def __init__(self, propName, typeFactory):
        """Creates a new typed property.

        The property stores its values in `obj.__dict__[propName]',
        but first converts them to a particular type by passing them
        to `typeFactory`.

        When retrieving values, the property uses the standard
        `getattr` function. If the resulting value is a string, it
        converts it using `typeFactory` before returning it. Despite
        some efficiency cost, this makes it possible to add typed
        properties to objects deep in `PropertyManager`'s
        `_getParent()` hierarchy, and still retrieve converted values
        for properties set in their parents.
        """
        self.propName = propName
        self.typeFactory = typeFactory

    def __get__(self, obj, type=None):
        value = obj._getAttrValue(self.propName)
        if isinstance(value, basestring):
            return self.typeFactory(value)
        else:
            return value

    def __set__(self, obj, value):
        obj.__dict__[self.propName] = self.typeFactory(value)

    def __delete__(self, obj):
        del obj.__dict__[self.propName]


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
