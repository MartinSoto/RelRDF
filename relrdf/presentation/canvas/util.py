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

from kiwi import tasklet

def task(generator):
    """A decorator to convert a function into a tasklet."""

    def wrapper(*args, **keywords):
        return tasklet.run(generator(*args, **keywords))

    return wrapper

def initTask(generator):
    """A decorator to convert an __init__ method into a tasklet.

    Creating an object with such an __init__ method will automatically
    start the task. If the object has a writable `_mainTask'
    attribute, it will be set to the task object."""

    def wrapper(self, *args, **keywords):
        taskObj = tasklet.run(generator(self, *args, **keywords))
        try:
            self._mainTask = taskObj
        except:
            pass

    return wrapper

def signalTask(generator):
    """A decorator to convert a signal handler into a tasklet.

    This traps exceptions happening in the generator and prints a
    stack trace.
    """
    def trapErrors(*args, **keywords):
        try:
            for val in generator(*args, **keywords):
                yield val
        except:
            import sys, traceback

            print >> sys.stderr, "Exception while executing signal task:"
            print >> sys.stderr, '-'*60
            traceback.print_exc(file=sys.stderr)
            print >> sys.stderr, '-'*60

    return task(trapErrors)

