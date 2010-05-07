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

Base code for command-line support in RelRDF backends
=====================================================



"""

import itertools
import optparse
import re
import sys

from relrdf.localization import _
from relrdf.error import CommandLineError

import help


class OptionParser(optparse.OptionParser):
    """A customized version of :class:`optparse.OptionParser` with
    modified error handling.
    """

    __slots__ = ()

    def error(self, msg):
        """Raise a :exc:`CommandLineError` exception with error
        message `msg`.
	"""
        raise CommandLineError(msg)


class CmdLineObject(object):
    """Base class for objects accessible from the command line through
    the ``relrdf`` command."""

    __slots__ = ('parser',)

    name = """<command>"""
    """Command name (mainly for user help)."""

    usage = _("%prog [OPTIONS]")
    """Usage syntax (for user help)."""

    def __init__(self):
        """The constructor runs the :meth:`makeParser` method and assigns the
        result to the :attr:`parser` attribute.
	"""

        self.parser = self.makeParser()
        """ This is the parser."""

    def makeParser(self):
        """Create and return and option parser for this operation.

	The default implementation returns an instance of
	:class:`optparse.OptionParser` with interspersed arguments
	disabled.

	Classes overriding this method should call the super method
	and add options to the returned parser.
	"""
        # We use the customized option parser.
        parser = OptionParser(prog=self.name, usage=self.usage,
                              add_help_option=False)
        parser.disable_interspersed_args()

        return parser

    @classmethod
    def summary(cls):
        """Return a one-line summary for the operation implemented by
	this object.

	The default implementation returns the first line of the
	class' docstring.
	"""
        text = cls.__doc__

        # Determine the end of the first line.
        pos = text.find('\n')

        if pos == -1:
            # The docstring consists of a single line.
            return text
        else:
            return text[:pos]

    def printHelpField(self, name, text, stream):
        """Print a help field.

	`name` is the field name, used as title. `text` is the text in
	the field, which may contain several paragraphs. `stream` is a
	file-like object to write the text to.
	"""
        # Write the field title.
        stream.write(name)
        stream.write(":")

        lines = list(help.wrapText(text, indent=2))

        if len(lines) == 0:
            # No text.
            stream.write('\n')
            return

        if len(lines) == 1 and \
                len(name) + len(lines[0]) <= help.getTerminalSize()[1] - 2:
            # Title and text fit in a single line.
            stream.write(' ')
            stream.write(lines[0][2:])
            stream.write('\n')
            return

        # Text under the title.
        stream.write('\n')
        for line in lines:
            sys.stdout.write(line)
            sys.stdout.write('\n')

    def help(self):
        """Print to standard output a help text for the operation
	implemented by this object.

	The default implementation of this method uses the class'
	docstring as a source for the help text. The docstring is
	stripped of its first line and "dedented" using the
	:func:`textwrap.dedent` function. Then the first line is prepended
	again and the result used as help text.
	"""
        stream = sys.stdout
        text = self.__class__.__doc__

        # Determine the end of the first line.
        pos = text.find('\n')

        # Print the purpose field.
        if pos == -1:
            # The docstring consists of a single line.
            purpose = text
        else:
            purpose = text[:pos + 1]
        self.printHelpField(_("Purpose"), purpose, stream)

        # Print the parser's help, containing usage and options.
        self.parser.print_help()
        stream.write('\n')

        # Print the command description field.
        self.printHelpField(_("Description"), text[pos + 1:], stream)


class CmdLineBackend(CmdLineObject):
    """Base class for command-line support in RelRDF backends."""

    __slots__ = ()

    identifier = None
    name = None

    def argsToConfig(self, cmdLineArgs):
        """Produce a modelbase configuration from the command-line
        specification in `cmdLineArgs`.

        `cmdLineArgs` is a list of strings. The first element always
        starts with ``::`` and identifies the modelbase type, e.g.,
        ``'::postgres'``. Subsequent elements are expected to be
        standard command-line options (that is, they start with ``-``)
        and their format is specific to each modelbase type.

        The set of arguments specifying the modelbase can (and often
        will be) followed by other, unrelated command-line
        arguments. This function parses the modelbase specification
        and returns any additional arguments untouched.

        The return value is a pair ``(mbConf, args)`` where ``mbConf``
        is the parsed configuration (an instance of
        :class:`relrdf.config.ModelbaseConfig`) and ``args`` is a list
        containing any remaining arguments.

        In case of error, this function raises :exc:`CommandLineError`
        with an appropriate error message.

	The default implementation parses the arguments using the
        options parser in this object, passes the resulting options
        object to the :meth:`optionsToConfig` method, and returns the
        resulting configuration together with all arguments left by
        the parser.
        """
        options, args = self.parser.parse_args(cmdLineArgs[1:])
        return (self.optionsToConfig(cmdLineArgs[0], options), args)

    def optionsToConfig(self, mbId, options):
        """Produce a modelbase configuration from a set of parsed
        options.

	This method is called by the default implementation of
	:meth:`argsToConfig` to convert parsed options into an actual
	modelbase configuration. `mbId` is the modelbase identifier
	passed as first argument to :meth:`argsToConfig` (e.g.,
	``'::postgres'``). `options` is the options object that
	resulted from running the option parser's `parse_args` method
	on the remaining modelbase command-line arguments. The return
	value is expected to be the modelbase configuration object
	corresponding to these identifier and options.

        In case of error, this function raises :exc:`CommandLineError`
        with an appropriate error message.
        """
        raise NotImplementedError

    def getOperation(self, name):
        raise NotImplementedError

    def getOperationNames(self):
        raise NotImplementedError


class CmdLineOperation(CmdLineObject):
    """Base class for the command-line operations (subcommands) of the
    ``relrdf`` command.
    """

    __slots__ = ()

    def makeParser(self):
        """Add a help option (:option:`-h` or :option:`--help`) to the
        parser created by the parent class.
	"""
        parser = super(CmdLineOperation, self).makeParser()

        parser.add_option('-h', '--help', action='store_true',
                          dest='help', default=False,
                          help=_("Show help message"))

        return parser

    def __call__(self, mbConf, cmdLineArgs):
        """Execute the operation implemented by this object.

	`mbConf` is a modelbase configuration, i.e., an instance of
	:class:`relrdf.config.ModelbaseConfig`. This represents the
	modelbase this operation is expected to work on. `cmdLineArgs`
	is a list of strings. The first element contains the operation
	name, while subsequent elements are expected to be standard
	command-line options (that is, they start with ``-``).  Option
	names and formats are specific to each particular operation.

	The return value is an integer that will be returned as status
	value by the :command:`relrdf` command when the operation is
	run.

	The default implementation parses the command-line arguments
	using the option parser stored in the :attr:`parser` attribute
	(see the standard :mod:`optparse` module) and passes the
	resulting options object and remaining arguments to the
	:meth:`run` method. If the help option (see method
	:meth:`makeParser`) is present in the argument list, the
	:meth:`help` method in this class will be called and
	:meth:`run` *will not* be called.
	"""
        options, args = self.parser.parse_args(cmdLineArgs[1:])
        if options.help:
            self.help()
            return 0
        return self.run(mbConf, options, args)

    def run(self, mbConf, options, args):
        """Execute the operation implemented by this object, after argument
        parsing.

	`mbConf` is a modelbase configuration, as received by the
	:meth:`__call__` method. `options` and `args` are the results
	of running the option parser's
	:method:`~optparse.OptionParser.parse_args` method on this
	operation's command-line arguments (see the :meth:`__call__`
	method.

	The return value is an integer that will be returned by the
	``relrdf`` command as status value when the operation is run.

	This is a convenience method that derived classes can
	implement in order to let this base class take care of
	argument parsing.
	"""
        raise NotImplementedError
