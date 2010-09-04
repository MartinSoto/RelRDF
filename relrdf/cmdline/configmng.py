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
    """Register a modelbase or model in the local registry

    Registers the modelbase or model specified by the modelbase and
    model arguments under the given NAME.

    This command can also be used to copy a configuration, by
    selecting it and registering it under a new target name.
    """

    __slots__ = ()

    name = 'register'
    usage = '%(prog)s NAME'

    def makeParser(self):
        parser = super(RegisterOperation, self).makeParser()

        parser.add_argument('--descr', '--description', '-d',
                            metavar=_("DESCR"), dest='descr', default='',
                            help=_("Use description DESCR for this "
                                   "modelbase (default: empty)"))
        parser.add_argument('name', metavar=_("NAME"),
                            help=_("NAME for the registered configuration"))

        return parser


    def run(self, options, mbConf=None, mbConfName=None, modelConf=None,
            registry=None, **kwArgs):
        if registry is None:
            registry = config.getDefaultRegistry()

        if modelConf is None:
            if mbConf is None:
                raise CommandLineError(_("No modelbase or model specified, "
                                         "nothing to register!"))

            path = (options.name,)
            conf = mbConf
        else:
            if mbConfName is None:
                raise CommandLineError(_("Cannot register model because "
                                         "no named modelbase was specified"))

            path = (mbConfName, options.name)
            conf = modelConf

        try:
            registry.setEntry(path, options.descr, conf)
        except ConfigurationError, e:
            raise CommandLineError(e)

        sys.stdout.write(_("Added entry '%s'") % options.name)

        return 0


class ListOperation(backend.CmdLineOperation):
    """List the registered modelbase or model names

    If no modelbase is specified, list modelbase names in alphabetical
    order, one per line. The current default modelbase, if any, will
    be marked with "(default). If a modelbase is specified by name,
    list the models in that modelbase."
    """

    __slots__ = ()

    name = 'list'
    usage = '%(prog)s'

    def run(self, options, mbConf=None, mbConfName=None, registry=None,
            **kwArgs):
        if registry is None:
            registry = config.getDefaultRegistry()

        if mbConf is None:
            path = ()
        else:
            if mbConfName is None:
                raise CommandLineError(_("No named modelbase configuration "
                                         "selected, nothing to list!"))

            path = (mbConfName,)

        try:
            default = registry.getDefaultName(path)
            names = list(registry.getEntryNames(path))
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
    """Remove a modelbase or model configuration from the local registry

    Removes the selected modelbase or model configuration from the
    registry. Only explicitly selected modelbases and models will be
    forgotten, this operation will not act on the defaults. 

    Notice that only the configuration will be removed but the
    referenced modelbase or model will not be affected in any way. If
    the configuration data is provided again (for example, by entering
    it manually), the referenced object should become accessible
    again.
    """

    __slots__ = ()

    name = 'forget'
    usage = '%(prog)s'

    def run(self, options, mbConf=None, mbConfName=None, modelConf=None, 
            modelConfName=None, registry=None, **kwArgs):
        if modelConfName is not None:
            path = (mbConfName, modelConfName)
        else:
            if modelConf is not None:
                raise CommandLineError(_("No named model configuration "
                                         "selected, nothing to forget!"))
            if mbConfName is None:
                raise CommandLineError(_("No named modelbase configuration "
                                         "selected, nothing to forget!"))
            path = (mbConfName,)

        try:
            registry.removeEntry(path)
        except ConfigurationError, e:
            raise CommandLineError(e)

        sys.stdout.write(_("Entry '%s' forgotten") % path[-1])

        return 0


class SetDefaultOperation(backend.CmdLineOperation):
    """Set the default modelbase and default models in the local registry

    The selected modelbase or model will become the default. The
    default modelbase is global, whereas models are set as default for
    their corresponding modelbases.
    """

    __slots__ = ()

    name = 'setdefault'
    usage = '%(prog)s'

    def run(self, options, mbConf=None, mbConfName=None, modelConf=None, 
            modelConfName=None, registry=None, **kwArgs):
        if modelConfName is not None:
            path = (mbConfName, modelConfName)
        else:
            if modelConf is not None:
                raise CommandLineError(_("No named model configuration "
                                         "selected, nothing to set as "
                                         "default!"))
            if mbConfName is None:
                raise CommandLineError(_("No named modelbase configuration "
                                         "selected, nothing to set as "
                                         "default!"))
            path = (mbConfName,)

        try:
            registry.setDefaultEntry(path)
        except ConfigurationError, e:
            raise CommandLineError(e)

        sys.stdout.write(_("'%s' is now the default entry") % path[-1])

        return 0
