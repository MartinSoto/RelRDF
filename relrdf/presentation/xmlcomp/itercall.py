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

"""An iterator composition system, allowing to easily simulate
procedure calls in generators and similar constructs.

The basis of the system is a simple iterator 'flatting'
algorithm. This algorithm takes an iterator and derives a new one
based on it. The derived iterator is identical to the original one
(produces the same values) except when the original one produces a
value which is an instance of the `Call` class in this module. When
this happens, the values produced by the iterator wrapped in the call
object are produced by the derived iterator instead of the `Call`
object itself. This behaviour is recursive, meaning that a called
iterator can itself return `Call` objects with the same behavior.

The `itertask` decorator can be used with generators or any other
functions returning iterators to automatically flatten the returned
iterators.
"""

class Call(object):
    """A wrapper object for an iterator, which tells the iterator
    flattener that the wrapped iterator must be exhausted first before
    continuing the execution of the current iterator. This actually
    simulates a procedure call for iterators."""
    __slots__ = ('called')

    def __init__(self, called):
        self.called = called


def iterflat(itr):
    """Iterator flattener."""
    stack = []

    while True:
        try:
            value = itr.next()
        except StopIteration:
            if len(stack) == 0:
                raise StopIteration
            else:
                itr = stack.pop()
                continue

        if isinstance(value, Call):
            stack.append(itr)
            itr = value.called
            continue

        yield value


def itertask(func):
    """A decorator for functions returning iterators, that flattens
    the returned values."""
    def wrapper(*args, **kwargs):
        return iterflat(func(*args, **kwargs))

    return wrapper

