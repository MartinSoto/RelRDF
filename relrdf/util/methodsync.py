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


import threading


class SyncMethodsMixin(object):
    """A mixing class that makes it possible to declare methods as
    synchonized.

    Synchronized methods are mutualy exclusive for a particular
    instance, that is, if one synchronized method is currently
    executing, attempts to start a second synchronized method from
    other threads will block until the method finishes. The
    `synchronized` decorator in this module marks methods as
    synchronized."""

    __slots__ = ('_methodLock')

    def __init__(self, *args, **keywords):
        super(SyncMethodsMixin, self).__init__(*args, **keywords)

        self._methodLock = threading.Lock()


def synchronized(method):
    """A decorator that makes a method synchronized.

    In order for this decorator to work, the class containing the
    method must inherit from the `SyncMethodsMixin` class in this
    module."""

    def wrapper(self, *args, **keywords):
        self._methodLock.acquire()
        try:
            return method(self, *args, **keywords)
        finally:
            self._methodLock.release()

    return wrapper
