# -*- coding: utf-8 -*-
# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2010 Fraunhofer-Institut fuer Experimentelles
#                         Software Engineering (IESE).
# Copyright (c) 2010      Martín Soto
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
Configuration support for the debugging backend
"""

from relrdf.localization import _

from relrdf.error import ConfigurationError
from relrdf.config import Configuration


class DebugModelConfiguration(Configuration):
    """Base class for all debugging model configurations."""

    __slots__ = ()


class DebugConfiguration(Configuration):
    """Debug configuration class.

    Used both for the modelbase and for the 'debug' model type.
    """

    __slots__ = ()

    name = 'debug'
    version = 1
    schema = {
        'foo': {
            'type': str,
            'default': 'The Real Foo',
            },
        'bar': {
            'type': int,
            'default': 42,
            },
        'baz': {
            'type': bool,
            'default': False,
            },
        }


class NullSinkConfiguration(DebugModelConfiguration):
    """Configuration class for the null sink."""

    __slots__ = ()
    
    name = 'null'
    version = 1
    schema = {}


class PrintSinkConfiguration(DebugModelConfiguration):
    """Configuration class for the print sink."""

    __slots__ = ()
    
    name = 'print'
    version = 1
    schema = {}


class ListSinkConfiguration(DebugModelConfiguration):
    """Configuration class for the list sink."""

    __slots__ = ()
    
    name = 'list'
    version = 1
    schema = {}


class DictSinkConfiguration(DebugModelConfiguration):
    """Configuration class for the dict sink."""

    __slots__ = ()
    
    name = 'dict'
    version = 1
    schema = {}



def getConfigClass(path):
    path = tuple(path)

    if path == ():
        return DebugConfiguration
    elif path == ('debug',):
        # Use the same configuration class as the modelbase.
        return DebugConfiguration
    elif path == ('null',):
        return NullSinkConfiguration
    elif path == ('print',):
        return PrintSinkConfiguration
    elif path == ('list',):
        return ListSinkConfiguration
    elif path == ('dict',):
        return DictSinkConfiguration
    else:
        raise InstantiationError(_("'%s' is not a valid model type for "
                                   "modelbase 'debug'" % path[0]))
