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
Configuration support for the debugging backend
"""

from relrdf.error import ConfigurationError
from relrdf.config import Configuration


class DebugConfiguration(Configuration):
    """Debug configuration class.
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


def getConfigClass(path):
    if len(path) == 0:
        return DebugConfiguration
    else:
        raise InstantiationError("'%s' is not a valid model type for a "
                                 "debug modelbase" % path[0])
