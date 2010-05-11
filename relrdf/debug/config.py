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

from relrdf import config
from relrdf.error import ConfigurationError


class DebugConfig(config.ModelbaseConfig):
    """Debug configuration object.
    """

    __slots__ = ('foo',
                 'bar',
                 'baz')

    def __init__(self, foo='The Real Foo', bar=39, baz=False):
        self.foo = foo
        self.bar = bar
        self.baz = baz

    @staticmethod
    def thaw(version, configData):
        if version > 1:
            raise ConfigurationError("Version %d of config data is not "
                                     "supported. Upgrade RelRDF" % version)
        return DebugConfig(configData['foo'], configData['bar'],
                           configData['baz'])

    def freeze(self):
        return (
            'debug',
            1,
            { 'foo': self.foo,
              'bar': self.bar,
              'baz': self.baz, })

    def getModelbase(self):
        raise NotImplementedError

