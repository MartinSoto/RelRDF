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

from relrdf.error import InstantiationError
from relrdf.cmdline import CmdLineObject

import config


class DebugCmdLineObj(CmdLineObject):
    __slots__ = ()

    name = 'debug'
    description = "Options to access the debug backend"

    configClass = config.DebugConfiguration

    def makeParser(self):
        parser = super(DebugCmdLineObj, self).makeParser()

        parser.add_argument('--foo', metavar="STRING", type=str,
                            help="Set first segment of the FUBAR "
                            "access block to STRING")
        parser.add_argument('--bar', metavar="INT", type=int,
                            help="Set second segment of the FUBAR "
                            "access block to INT")
        parser.add_argument('--baz', action='store_true',
                            help="Use the BAZ data subblock if available")

        return parser


def getCmdLineObject(path):
    path = tuple(path)

    # Use the same configuration class at all levels.
    if path == ():
        return DebugCmdLineObj()
    elif path == ('debug',):
        return DebugCmdLineObj()
    else:
        raise InstantiationError("invalid object path %s" % repr(path))
