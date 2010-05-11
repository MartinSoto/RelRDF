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

"""Test the basic set of command-line operations.
"""

import unittest
import os, tempfile, shutil, subprocess

from relrdf import config
from relrdf.debug import DebugConfig


class BasicTestCase(unittest.TestCase):
    """Basic test case for accessing the modelbase registry from the
    command line."""

    def setUp(self):
        # Clean up the environment.
        try:
            del os.environ['HOME']
        except KeyError:
            pass
        try:
            del os.environ['XDG_DATA_HOME']
        except KeyError:
            pass
        try:
            del os.environ['RELRDF_CONFIG']
        except KeyError:
            pass

        # Create a directory.
        self.dir = tempfile.mkdtemp()

        # Make the config file location point to the directory.
        os.environ['RELRDF_CONFIG'] = os.path.join(self.dir, 'config.json')

    def tearDown(self):
        shutil.rmtree(self.dir)
        del os.environ['RELRDF_CONFIG']

    def getRegistry(self):
        """Return a new registry object that uses the same
        configuration used by the tested command-line programs."""
        return config.ModelbaseRegistry()

    def _runCommand(self, cmdLine):
        relrdfProg = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         '..', 'bin', 'relrdf'))

        p = subprocess.Popen([relrdfProg] + cmdLine, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        return p.returncode, stdout, stderr

    def checkCommand(self, cmdLine):
        status, stdout, stderr = self._runCommand(cmdLine)

        if status != 0:
            if len(stderr) == 0:
                self.assertEqual(status, 0, "Success expected, but error "
                                 "status %d was returned" % status)
            else:
                self.assertEqual(status, 0, "Success expected, but command "
                                 "execution failed with status %d. "
                                 "Error message folows:\n\n%s" %
                                 (status, stderr))

        if len(stderr) > 0:
            self.fail("Succesful command wrote to stderr. Error message "
                      "follows:\n\n%s" % stderr)

        return stdout

    def checkCommandError(self, cmdLine):
        status, stdout, stderr = self._runCommand(cmdLine)
        self.assertNotEqual(status, 0, "Failure expected, but success "
                            "status was returned")
        self.assertTrue(len(stderr) > 0, "Failed command did not write "
                        "to stderr")

        if "+++ Exception +++" in stderr:
            self.fail("Command failed with an exception:\n\n%s" % stderr)

        return status, stdout, stderr


class MainCommandTestCase(BasicTestCase):
    def testNoArgs(self):
        self.checkCommand([])

    def testInexistent(self):
        self.checkCommandError(['norealcommand'])


class HelpTestCase(BasicTestCase):
    """Test the help operation."""

    def testGeneralHelp(self):
        self.checkCommand(['help'])

    def testHelpCommand(self):
        self.checkCommand(['help', 'help'])

    def testMinusH(self):
        self.checkCommand(['help', '-h'])

    def testHelpInexistent(self):
        self.checkCommandError(['help', 'norealcommand'])


class RegisterTestCase(BasicTestCase):
    """Test the register operation."""

    def testHelp(self):
        self.checkCommand(['register', '-h'])

    def testRegister1(self):
        stdout = self.checkCommand(['::debug', '--foo=theFoo', '--bar=43',
                                    '--baz', 'register', 'entry1'])

        self.assertTrue('entry1' in stdout)

        reg = self.getRegistry()
        self.assertEqual(set(reg.getEntryNames()), set(['entry1']))
        descr, config = reg.getEntry('entry1')
        self.assertEqual(descr, '')
        self.assertEqual(config.foo, 'theFoo')
        self.assertEqual(config.bar, 43)
        self.assertTrue(config.baz)

    def testRegister2(self):
        # Make sure that the registry isn't overwritten by a second
        # command.
        self.checkCommand(['::debug', '--foo=theFoo', '--bar=43',
                           '--baz', 'register', 'entry1'])
        self.checkCommand(['::debug', '--foo=anotherFoo', 'register',
                           'entry2'])

        reg = self.getRegistry()
        self.assertEqual(set(reg.getEntryNames()), set(['entry1', 'entry2']))
        descr, config = reg.getEntry('entry1')
        self.assertEqual(descr, '')
        self.assertEqual(config.foo, 'theFoo')
        self.assertEqual(config.bar, 43)
        self.assertTrue(config.baz)

    def testRegisterDescr(self):
        descrText = 'The description'
        self.checkCommand(['::debug', '--foo=theFoo', 'register', 
                           '-d', descrText, 'entry1'])

        reg = self.getRegistry()
        self.assertEqual(set(reg.getEntryNames()), set(['entry1']))
        descr, config = reg.getEntry('entry1')
        self.assertEqual(descr, descrText)
        self.assertEqual(config.foo, 'theFoo')
        self.assertEqual(config.bar, 42)
        self.assertFalse(config.baz)

    def testNoModelbase(self):
        self.checkCommandError(['register', 'entry1'])

    def testNoName(self):
        self.checkCommandError(['::debug', 'register'])

    def testManyOptions(self):
        self.checkCommandError(['::debug', 'register', 'entry1', 'entry2'])


class ListTestCase(BasicTestCase):
    """Test the list operation."""

    def testHelp(self):
        self.checkCommand(['list', '-h'])

    def testListNone(self):
        stdout = self.checkCommand(['list'])
        self.assertTrue(len(stdout) == 0)

    def testListOne(self):
        reg = self.getRegistry()
        reg.setEntry('entry1', '', DebugConfig())
        del reg

        self.assertEqual(self.checkCommand(['list']), 'entry1\n')

    def testListTwo(self):
        reg = self.getRegistry()
        reg.setEntry('entry2', '', DebugConfig())
        reg.setEntry('entry1', '', DebugConfig())
        del reg

        self.assertEqual(self.checkCommand(['list']),
                         'entry1\nentry2\n')

    def testListOneDefault(self):
        reg = self.getRegistry()
        reg.setEntry('entry1', '', DebugConfig())
        reg.setDefaultEntry('entry1')
        del reg

        self.assertEqual(self.checkCommand(['list']), 'entry1 (default)\n')

    def testListTwoDefault(self):
        reg = self.getRegistry()
        reg.setEntry('entry2', '', DebugConfig())
        reg.setEntry('entry1', '', DebugConfig())
        reg.setDefaultEntry('entry2')
        del reg

        self.assertEqual(self.checkCommand(['list']),
                         'entry1\nentry2 (default)\n')

    def testWithOptions(self):
        self.checkCommandError(['list', 'someoption'])


class ForgetTestCase(BasicTestCase):
    """Test the forget operation."""

    def testHelp(self):
        self.checkCommand(['forget', '-h'])

    def testForget1(self):
        reg = self.getRegistry()
        reg.setEntry('entry1', '', DebugConfig())
        reg.setDefaultEntry('entry1')
        del reg

        stdout = self.checkCommand([':entry1', 'forget'])

        self.assertTrue('entry1' in stdout)

    def testForget2(self):
        reg = self.getRegistry()
        reg.setEntry('entry1', '', DebugConfig(bar=14))
        reg.setEntry('entry2', '', DebugConfig())
        reg.setEntry('entry3', '', DebugConfig())
        reg.setDefaultEntry('entry1')
        del reg

        self.checkCommand([':entry3', 'forget'])
        self.checkCommand([':entry2', 'forget'])

        reg = self.getRegistry()
        self.assertEqual(set(reg.getEntryNames()), set(['entry1']))
        descr, config = reg.getEntry('entry1')
        self.assertEqual(config.bar, 14)

    def testForgetDefault(self):
        reg = self.getRegistry()
        reg.setEntry('entry1', '', DebugConfig(bar=14))
        reg.setEntry('entry2', '', DebugConfig())
        reg.setEntry('entry3', '', DebugConfig())
        reg.setDefaultEntry('entry2')
        del reg

        self.checkCommand(['forget'])

        reg = self.getRegistry()
        self.assertEqual(set(reg.getEntryNames()),
                         set(['entry1', 'entry3']))
        descr, config = reg.getEntry('entry1')
        self.assertEqual(config.bar, 14)        

    def testForgetInexistent(self):
        self.checkCommandError([':entry1', 'forget'])

    def testForgetExplicit(self):
        self.checkCommandError(['::debug', 'forget'])

    def testNoModelbase(self):
        self.checkCommandError([':entry1', 'forget'])

    def testWithOptions(self):
        self.checkCommandError(['forget', 'someoption'])


class SetDefaultTestCase(BasicTestCase):
    """Test the set default operation."""

    def testHelp(self):
        self.checkCommand(['setdefault', '-h'])

    def testSetDefault1(self):
        reg = self.getRegistry()
        reg.setEntry('entry1', '', DebugConfig())
        del reg

        stdout = self.checkCommand([':entry1', 'setdefault'])

        self.assertTrue('entry1' in stdout)

        reg = self.getRegistry()
        self.assertEqual(reg.getDefaultName(), 'entry1')

    def testSetDefault2(self):
        reg = self.getRegistry()
        reg.setEntry('entry1', '', DebugConfig(bar=14))
        reg.setEntry('entry2', '', DebugConfig())
        reg.setEntry('entry3', '', DebugConfig())
        del reg

        self.checkCommand([':entry3', 'setdefault'])

        reg = self.getRegistry()
        self.assertEqual(reg.getDefaultName(), 'entry3')

        self.checkCommand([':entry2', 'setdefault'])

        reg = self.getRegistry()
        self.assertEqual(reg.getDefaultName(), 'entry2')

    def testSetDefaultDefault(self):
        reg = self.getRegistry()
        reg.setEntry('entry1', '', DebugConfig(bar=14))
        reg.setEntry('entry2', '', DebugConfig())
        reg.setEntry('entry3', '', DebugConfig())
        reg.setDefaultEntry('entry2')
        del reg

        self.checkCommand(['setdefault'])

        reg = self.getRegistry()
        self.assertEqual(reg.getDefaultName(), 'entry2')

    def testSetDefaultInexistent(self):
        self.checkCommandError([':entry1', 'setdefault'])

    def testSetDefaultExplicit(self):
        self.checkCommandError(['::debug', 'setdefault'])

    def testNoModelbase(self):
        self.checkCommandError([':entry1', 'setdefault'])

    def testWithOptions(self):
        self.checkCommandError(['setdefault', 'someoption'])
