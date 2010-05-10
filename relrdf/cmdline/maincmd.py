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

The main ``relrdf`` command
===========================

"""

import sys
from os import path

from relrdf.localization import _
from relrdf.error import CommandLineError, ConfigurationError
from relrdf import modelbasefactory
from relrdf import config

import backend
import help


def helpMessage(cmdName):
    """Print a basic help message for the main command. `cmdName`
    contains the name originally used to call the command."""
    print _(
"""
relrdf ::MBTYPE [MBARG...] SUBCOMMAND [ARG...]

or

relrdf :MBNAME SUBCOMMAND [ARG...]

or

relrdf SUBCOMMAND [ARG...]
"""
        )


class HelpOperation(backend.CmdLineOperation):
    """Print detailed help about the relrdf command and its operations

    Without arguments, lists all available operations. With an
    OPERATION name, provides help about that operation.
    """

    name = 'help'
    usage = '%prog [OPERATION]'

    def run(self, options, args, **kwArgs):
        if len(args) == 0:
            sys.stdout.write(_("RelRDF - A system for storage, analysis and"
                               " comparison of RDF models\n"))
            sys.stdout.write("https://launchpad.net/relrdf\n\n")
            sys.stdout.write(_("Operations:\n"))

            names = list(operationNames)
            names.sort()
            indent = max(map(len, names)) + 4
            for name in names:
                for line in help.wrapText(getOperation(name).summary(),
                                          indent=indent,
                                          firstIndent='  ' + name):
                    sys.stdout.write(line)
                    sys.stdout.write('\n')
        elif len(args) == 1:
            operation = getOperation(args[0])
            if operation is None:
                raise CommandLineError(_("Unknown operation '%s'") % args[0])
            operation.help()
        else:
            raise CommandLineError(_("Too many arguments"))


# List of operation names.
operationNames = [
    'help',
    'register',
    ]

def getOperation(name):
    """Retrieve the operation instance identified by name `name`.

    Returns `None` if the operation does not exist.
    """

    # This is implemented this way in order to import only the modules
    # that are required to run each command. Import time can have a
    # significant impact on program startup.

    if name == 'help':
        return HelpOperation()
    if name == 'register':
        import configmng
        return configmng.RegisterOperation()
    else:
        return None


def mainCmd(args):
    """
    Implementation of RelRDF's main command (typically called
    :cmd:``relrdf``).

    `args` contains the list of command-line arguments, with the name
    used to invoke the command in the first position. The return value
    is an integer to be returned to the operating system as a process
    status.
    """

    cmdName = path.basename(args[0])
    args = args[1:]

    if len(args) == 0:
        helpMessage(cmdName)
        return 0

    mbConf = None
    registry = None

    try:
        if args[0].startswith('::'):
            # We have an explicit modelbase specification, parse it.
            backend = modelbasefactory.getCmdLineBackend(args[0][2:])
            mbConf, args = backend.argsToConfig(args)
        elif args[0].startswith(':'):
            # We have a named modelbase configuration, retrieve it from
            # the default registry.
            try:
                registry = config.getDefaultRegistry()
                mbConf = registry.getEntry(args[0][1:])
            except ConfigurationError, e:
                raise CommandLineError(str(e))

            # Get rid of the first argument.
            args = args[1:]

        # The first argument must now be an operation name.
        if len(args) == 0:
            raise CommandLineError(_("No operation name specified"))

        # Retrieve the operation.
        operation = getOperation(args[0])
        if operation is None:
            raise CommandLineError(_("Unknown operation '%s'") % args[0])

        # Run the operation.
        if operation.needsMbConf:
            if mbConf is None:
                # No explicit modelbase configuration was specified,
                # try to use the default configuration.
                try:
                    registry = config.getDefaultRegistry()
                    mbConf = registry.getEntry()
                except ConfigurationError, e:
                    raise CommandLineError(_("Command '%s' requires a "
                                             "modelbase but none was "
                                             "specified (and no default "
                                             "is set)" %
                                             operation.name))

            return operation(args, registry=registry, mbConf=mbConf)
        else:
            return operation(args)
    except CommandLineError, e:
        print >> sys.stderr, '%s: %s' % (cmdName, str(e))
        return 1
