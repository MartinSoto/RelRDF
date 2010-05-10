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
Command-line operations for managing modelbase configurations
"""

from relrdf.localization import _
from relrdf import config

import backend


class RegisterOperation(backend.CmdLineOperation):
    """Register a modelbase in the local registry

    The selected modelbase will be registered under the given
    NAME.

    This command can also be used to copy a modelbase
    configuration, by selecting the source configuration and
    registering it under a new target name.
    """

    __slots__ = ()

    name = 'register'
    usage = 'register NAME'

    needsMbConf = True

    def makeParser(self):
        parser = super(RegisterOperation, self).makeParser()

        parser.add_option('--descr', '--description', '-d',
                          metavar=_("DESCR"), action='store',
                          type='string', dest='descr', default='',
                          help=_("Use description DESCR for this "
                                 "modelbase"))

        return parser

    def run(self, options, args, mbConf, registry=None, **kwArgs):
        if registry is None:
            registry = config.getDefaultRegistry()
