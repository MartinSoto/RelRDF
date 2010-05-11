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

import sys

from relrdf.localization import _
from relrdf.error import CommandLineError, ConfigurationError
from relrdf import config

import backend


class RegisterOperation(backend.CmdLineOperation):
    """Register a modelbase in the local registry

    Registers the selected modelbase under the given NAME.

    This command can also be used to copy a modelbase
    configuration, by selecting the source configuration and
    registering it under a new target name.
    """

    __slots__ = ()

    name = 'register'
    usage = '%prog NAME'

    needsMbConf = True

    def makeParser(self):
        parser = super(RegisterOperation, self).makeParser()

        parser.add_option('--descr', '--description', '-d',
                          metavar=_("DESCR"), action='store',
                          type='string', dest='descr', default='',
                          help=_("Use description DESCR for this "
                                 "modelbase (default: empty)"))

        return parser


    def run(self, options, args, mbConf, registry=None, **kwArgs):
        if len(args) == 0:
            raise CommandLineError(_("No name specified"))
        elif len(args) > 1:
            raise CommandLineError(_("Too many arguments"))

        if registry is None:
            registry = config.getDefaultRegistry()

        try:
            registry.setEntry(args[0], options.descr, mbConf)
        except ConfigurationError, e:
            raise CommandLineError(e)

        sys.stdout.write(_("Added entry '%s'") % args[0])

        return 0


class ListOperation(backend.CmdLineOperation):
    """List the modelbase names in the local registry

    List modelbase names in alphabetical order, one per line. The
    current default modelbase, if any, will be marked with "(default)"
    """

    __slots__ = ()

    name = 'list'
    usage = '%prog NAME'

    def run(self, options, args, registry=None, **kwArgs):
        if len(args) > 0:
            raise CommandLineError(_("Too many arguments"))

        if registry is None:
            registry = config.getDefaultRegistry()

        try:
            default = registry.getDefaultName()
            names = list(registry.getEntryNames())
            names.sort()
            for name in names:
                sys.stdout.write(name)
                if name == default:
                    sys.stdout.write(' (default)')
                sys.stdout.write('\n')
        except ConfigurationError, e:
            raise CommandLineError(e)

        return 0


class ForgetOperation(backend.CmdLineOperation):
    """Remove a modelbase configuration from the local registry

    Removes the selected modelbase.

    The modelbase will only be removed from the local registry (i.e.,
    it will be forgotten) but not destroyed. If the configuration data
    is (manually) provided again, the modelbase should still be
    accessible.
    """

    __slots__ = ()

    name = 'forget'
    usage = '%prog'

    needsMbConf = True

    def run(self, options, args, registry=None, mbConfName=None, **kwArgs):
        if len(args) > 0:
            raise CommandLineError(_("Too many arguments"))

        if mbConfName is None:
            raise CommandLineError(_("No stored modelbase selected, "
                                     "nothing to forget!"))

        try:
            registry.removeEntry(mbConfName)
        except ConfigurationError, e:
            raise CommandLineError(e)

        sys.stdout.write(_("Entry '%s' forgotten") % mbConfName)

        return 0
