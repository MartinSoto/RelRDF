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
import itertools

from relrdf.localization import _
from relrdf.error import CommandLineError, ConfigurationError
from relrdf import centralfactory
from relrdf import config

import parser as parsermod
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
    usage = '%(prog)s [OPERATION]'

    def makeParser(self):
        parser = super(HelpOperation, self).makeParser()

        parser.add_argument('operation', nargs='?',
                            help=_("Operation name"))

        return parser

    def run(self, options, **kwArgs):
        if options.operation is None:
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
        else:
            operation = getOperation(options.operation)
            if operation is None:
                raise CommandLineError(_("Unknown operation '%s'") %
                                       options.operation)
            operation.help()


# List of operation names.
operationNames = [
    'help',
    'import',
    'list',
    'register',
    'setdefault',
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
    if name == 'list':
        import configmng
        return configmng.ListOperation()
    if name == 'forget':
        import configmng
        return configmng.ForgetOperation()
    if name == 'setdefault':
        import configmng
        return configmng.SetDefaultOperation()
    if name == 'import':
        import importfile
        return importfile.ImportOperation()
    else:
        return None

def makeMbParser():
    parser = parsermod.ArgumentParser(add_help=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--mb', '--modelbase', action='store')
    group.add_argument('--mbtype', '--modelbasetype', action='store')

    return parser

mbParser = makeMbParser()

def makeModelParser():
    parser = parsermod.ArgumentParser(add_help=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--model', action='store')
    group.add_argument('--modeltype', action='store')

    return parser

modelParser = makeModelParser()


def mainCmd(args):
    """
    Implementation of RelRDF's main command (typically called
    :cmd:``relrdf``).

    `args` contains the list of command-line arguments, with the name
    used to invoke the command in the first position. The return value
    is an integer to be returned to the operating system as a process
    status.
    """
    try:
        cmdName = path.basename(args[0])
        args = args[1:]

        if len(args) == 0:
            helpMessage(cmdName)
            return 0

        registry = config.getDefaultRegistry()

        mbConf = None
        mbConfName = None
        if args[0][0] == '-':
            options, args = mbParser.parse_known_args(args, contiguous=True)
            if options.mb is not None:
                # We have a named modelbase configuration, retrieve it from
                # the default registry.
                try:
                    descr, mbConf = registry.getEntry((options.mb,))
                    mbConfName = options.mb
                except ConfigurationError, e:
                    raise CommandLineError(str(e))
            elif options.mbtype is not None:
                # We have an explicit modelbase specification, parse it:
                try:
                    cmdLineObj = centralfactory. \
                        getCmdLineObject((options.mbtype,))
                    mbConf, args = cmdLineObj.argsToConfig(args)
                except ConfigurationError, e:
                    raise CommandLineError(str(e))

        modelConf = None
        modelConfName = None
        if args[0][0] == '-':
            options, args = modelParser.parse_known_args(args, contiguous=True)
            if options.model is not None:
                # We have a named model configuration.

                if mbConfName is None and mbConf is not None:
                    raise CommandLineError(_("A named model configuration "
                                             "is not allowed for an "
                                             "explicit modelbase "
                                             "configuration"))

                # Retrieve it from the default registry.
                try:
                    descr, modelConf = registry.getEntry((mbConfName,
                                                          options.model))
                    modelConfName = options.model
                except ConfigurationError, e:
                    raise CommandLineError(str(e))
            elif options.modeltype is not None:
                # We have an explicit model specification.
                try:
                    # In order to obtain the configuration class for the
                    # model, we require the modelbase type. It can always
                    # be obtained from the current modelbase config, but
                    # we may not have one as yet.
                    if mbConf is None:
                        # Use the default modelbase configuration.
                        mbConfName = registry.getDefaultName(())
                        if mbConfName is None:
                            raise CommandLineError(
                                _("An explicit model configuration requires "
                                  "a modelbase but none was specified "
                                  "(and no default is set)" % self.name))
                            pass
                        descr, mbConf = registry.getEntry((mbConfName,))

                    cmdLineObj = centralfactory. \
                        getCmdLineObject((mbConf.name,
                                          options.modeltype,))
                    modelConf, args = cmdLineObj.argsToConfig(args)
                except ConfigurationError, e:
                    raise CommandLineError(str(e))

        # The first argument must now be an operation name.
        if len(args) == 0:
            raise CommandLineError(_("No operation name specified"))
        if args[0][0] == '-':
            raise CommandLineError(_("Unrecognized option '%s' "
                                     "(or maybe it is just "
                                     "misplaced...)") % args[0])

        # if mbConf is None:
        #     print "No modelbase configuration"
        #     print
        # else:
        #     print "Modelbase config:"
        #     print mbConf.readableContents()
        # if modelConf is None:
        #     print "No model configuration"
        # else:
        #     print "Model config:"
        #     print modelConf.readableContents()

        # Retrieve the operation.
        opName = args[0]
        operation = getOperation(opName)
        if operation is None:
            raise CommandLineError(_("Unknown operation '%s'") % opName)

        # Prepare the internal operation arguments.
        kwargs = {'registry': registry}

        if mbConf is not None:
            kwargs['mbConf'] = mbConf
            kwargs['mbConfName'] = mbConfName
        else:
            if operation.needsMbConf:
                # No explicit modelbase configuration was specified,
                # try to use the default configuration.
                try:
                    descr, kwargs['mbConf'] = registry.getEntry((None,))
                    kwargs['mbConfName'] = registry.getDefaultName(())
                except ConfigurationError:
                    # No modelbase available.
                    pass

        if modelConf is not None:
            kwargs['modelConf'] = modelConf
            kwargs['modelConfName'] = modelConfName
        else:
            if operation.needsModelConf:
                # No explicit model configuration was specified, try
                # to use the default configuration.
                try:
                    descr, kwargs['modelConf'] = registry.getEntry(
                        (mbConfName, None))
                    kwargs['modelConfName'] = registry.getDefaultName(
                        (mbConfName,))
                except ConfigurationError:
                    # No model available.
                    pass
                
        # Run the operation.
        return operation(args, **kwargs)
    except CommandLineError, e:
        print >> sys.stderr, '%s: %s' % (cmdName, str(e))
        return 1
