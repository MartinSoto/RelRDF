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
Command-line support for the debugging backend
"""

from optparse import OptionParser

from relrdf.error import ConfigurationError
from relrdf.cmdline import backend

import config


class DebugBackend(backend.CmdLineBackend):
    """Debug command-line backend.
    """

    __slots__ = ()

    identifier = 'debug'
    name = 'Debug backend'

    def makeParser(self):
        parser = super(DebugBackend, self).makeParser()

        parser.add_option('--foo', metavar="STRING", action='store',
                          type='string', dest='foo', default='slatfatf',
                          help="Set first segment of the FUBAR "
                          "access block to STRING")
        parser.add_option('--bar', metavar="INT", action='store',
                          type='int', dest='bar', default=42,
                          help="Set second segment of the FUBAR "
                          "access block to INT")
        parser.add_option('--baz', action='store_true',
                          dest='baz', default=False,
                          help="Use the BAZ data subblock if available")

        return parser

    def optionsToConfig(self, mbId, options):
        assert mbId == '::debug'
        return config.DebugConfig(options.foo, options.bar, options.baz)

    def getOperation(self, name):
        raise NotImplementedError

    def getOperationNames(self):
        raise NotImplementedError


# Singleton instance.
cmdLineBackend = DebugBackend()
