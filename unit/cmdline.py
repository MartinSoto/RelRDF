# -*- coding: utf-8 -*-
# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2010 Fraunhofer-Institut fuer Experimentelles
#                         Software Engineering (IESE).
# Copyright (c) 2010      Martín Soto
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
import os, tempfile, shutil, subprocess, hashlib

from relrdf import config
from relrdf.debug import DebugConfiguration


class BasicTestCase(unittest.TestCase):
    """Basic test case for accessing the registry from the command
    line.
    """

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

        # Object selection values. They can be changed to run particular
        # tests at different levels of the configuration hierarchy.
        # See also method getSelArgs.
        self.pathPrefix = ()
        self.selPrefix = []
        self.selOpt = 'mb'
        self.typePrefix = self.selPrefix + ['--mbtype=debug']

        # Object selection options. They can be changed so that the
        # command is always run with these selection options.
        self.selOp# -*- Python -*-
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
import os, tempfile, shutil, subprocess, hashlib

from relrdf import config
from relrdf.debug import DebugConfiguration


class BasicTestCase(unittest.TestCase):
    """Basic test case for accessing the registry from the command
    line.
    """

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

        # Object selection values. They can be changed to run particular
        # tests at different levels of the configuration hierarchy.
        # See also method getSelArgs.
        self.pathPrefix = ()
        self.selPrefix = []
        self.selOpt = 'mb'
        self.typePrefix = self.selPrefix + ['--mbtype=debug']

        # Object selection options. They can be changed so that the
        # command is always run with these selection options.
        self.selOptions = []

    def tearDown(self):
        shutil.rmtree(self.dir)
        del os.environ['RELRDF_CONFIG']

    def getRegistry(self):
        """Return a new registry object that uses the same
        configuration used by the tested command-line programs."""
        return config.Registry()

    def _runCommand(self, cmdLine):
        relrdfProg = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         '..', 'bin', 'relrdf'))

        p = subprocess.Popen([relrdfProg] + self.selOptions + cmdLine,
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
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

    def getSelArgs(self, name):
        """Returns the command-line arguments necessary to select
        entry `name`."""
        return self.selPrefix + ['--%s=%s' % (self.selOpt, name)]


class ModelTestCase(BasicTestCase):
    """Basic test case adapted to run at the model level."""

    def setUp(self):
        super(ModelTestCase, self).setUp()

        # Object selection values for the model level.
        self.pathPrefix = ('baseentry',)
        self.selPrefix = ['--mb=baseentry']
        self.selOpt = 'model'
        self.typePrefix = self.selPrefix + ['--modeltype=debug']        

        # Add the base modelbase config. All tests will run using this
        # configuration as a parent.
        reg = self.getRegistry()
        reg.setEntry(self.pathPrefix, '', DebugConfiguration())


class ModelMbDefTestCase(BasicTestCase):
    """Basic test case adapted to run at the model level, using the
    default modelbase."""

    def setUp(self):
        super(ModelMbDefTestCase, self).setUp()

        # Object selection values for the model level.
        self.pathPrefix = ('baseentry',)
        self.selPrefix = []
        self.selOpt = 'model'
        self.typePrefix = self.selPrefix + ['--modeltype=debug']        

        # Add the base modelbase config. All tests will run using this
        # configuration as a parent.
        reg = self.getRegistry()
        reg.setEntry(self.pathPrefix, '', DebugConfiguration())
        reg.setDefaultEntry(self.pathPrefix)


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
        stdout = self.checkCommand(self.typePrefix +
                                   ['--foo=theFoo', '--bar=43',
                                    '--baz', 'register', 'entry1'])

        self.assertTrue('entry1' in stdout)

        reg = self.getRegistry()
        self.assertEqual(set(reg.getEntryNames(self.pathPrefix)),
                         set(['entry1']))
        descr, config = reg.getEntry(self.pathPrefix + ('entry1',))
        self.assertEqual(descr, '')
        self.assertEqual(config.getParam('foo'), 'theFoo')
        self.assertEqual(config.getParam('bar'), 43)
        self.assertTrue(config.getParam('baz'))

    def testRegister2(self):
        # Make sure that the registry isn't overwritten by a second
        # command.
        self.checkCommand(self.typePrefix +
                          ['--foo=theFoo', '--bar=43',
                           '--baz', 'register', 'entry1'])
        self.checkCommand(self.typePrefix +
                          ['--foo=anotherFoo', 'register', 'entry2'])

        reg = self.getRegistry()
        self.assertEqual(set(reg.getEntryNames(self.pathPrefix)),
                         set(['entry1', 'entry2']))
        descr, config = reg.getEntry(self.pathPrefix + ('entry1',))
        self.assertEqual(descr, '')
        self.assertEqual(config.getParam('foo'), 'theFoo')
        self.assertEqual(config.getParam('bar'), 43)
        self.assertTrue(config.getParam('baz'))

    def testRegisterDescr(self):
        descrText = 'The description'
        self.checkCommand(self.typePrefix +
                          ['--foo=theFoo', 'register', '-d', descrText,
                           'entry1'])

        reg = self.getRegistry()
        self.assertEqual(set(reg.getEntryNames(self.pathPrefix)),
                         set(['entry1']))
        descr, config = reg.getEntry(self.pathPrefix + ('entry1',))
        self.assertEqual(descr, descrText)
        self.assertEqual(config.getParam('foo'), 'theFoo')
        self.assertEqual(config.getParam('bar'), 42)
        self.assertFalse(config.getParam('baz'))

    def testNoModelbase(self):
        self.checkCommandError(['register', 'entry1'])

    def testNoName(self):
        self.checkCommandError(self.typePrefix + ['register'])

    def testManyOptions(self):
        self.checkCommandError(self.typePrefix +
                               ['register', 'entry1', 'entry2'])


class ModelRegisterTestCase(ModelTestCase, RegisterTestCase):
    """Test the register operation at the model level."""

    def testNoNamedModelbase(self):
        self.checkCommandError(['--mbtype=debug', '--modeltype=debug',
                                'register', 'entry1'])


class ModelMbDefRegisterTestCase(ModelMbDefTestCase, RegisterTestCase):
    """Test the register operation at the model level, using the
    default modelbase."""
    pass


class ListTestCase(BasicTestCase):
    """Test the list operation."""

    def testHelp(self):
        self.checkCommand(self.selPrefix + ['list', '-h'])

    def testListNone(self):
        stdout = self.checkCommand(self.selPrefix + ['list'])
        self.assertTrue(len(stdout) == 0)

    def testListOne(self):
        reg = self.getRegistry()
        reg.setEntry(self.pathPrefix + ('entry1',), '',
                     DebugConfiguration())
        del reg

        self.assertEqual(self.checkCommand(self.selPrefix + ['list']),
                         'entry1\n')

    def testListTwo(self):
        reg = self.getRegistry()
        reg.setEntry(self.pathPrefix + ('entry2',), '',
                     DebugConfiguration())
        reg.setEntry(self.pathPrefix + ('entry1',), '',
                     DebugConfiguration())
        del reg

        self.assertEqual(self.checkCommand(self.selPrefix + ['list']),
                         'entry1\nentry2\n')

    def testListOneDefault(self):
        reg = self.getRegistry()
        reg.setEntry(self.pathPrefix + ('entry1',), '',
                     DebugConfiguration())
        reg.setDefaultEntry(self.pathPrefix + ('entry1',))
        del reg

        self.assertEqual(self.checkCommand(self.selPrefix + ['list']),
                         'entry1 (default)\n')

    def testListTwoDefault(self):
        reg = self.getRegistry()
        reg.setEntry(self.pathPrefix + ('entry2',), '',
                     DebugConfiguration())
        reg.setEntry(self.pathPrefix + ('entry1',), '',
                     DebugConfiguration())
        reg.setDefaultEntry(self.pathPrefix + ('entry2',))
        del reg

        self.assertEqual(self.checkCommand(self.selPrefix + ['list']),
                         'entry1\nentry2 (default)\n')

    def testWithOptions(self):
        self.checkCommandError(['list', 'someoption'])


class ModelListTestCase(ModelTestCase, ListTestCase):
    """Test the list operation at the model level."""
    pass


class ForgetTestCase(BasicTestCase):
    """Test the forget operation."""

    def testHelp(self):
        self.checkCommand(['forget', '-h'])

    def testForget1(self):
        reg = self.getRegistry()
        reg.setEntry(self.pathPrefix + ('entry1',), '',
                     DebugConfiguration())
        reg.setDefaultEntry(self.pathPrefix + ('entry1',))
        del reg

        stdout = self.checkCommand(self.getSelArgs('entry1') + ['forget'])

        self.assertTrue('entry1' in stdout)

    def testForget2(self):
        reg = self.getRegistry()
        reg.setEntry(self.pathPrefix + ('entry1',), '',
                     DebugConfiguration(bar=14))
        reg.setEntry(self.pathPrefix + ('entry2',), '',
                     DebugConfiguration())
        reg.setEntry(self.pathPrefix + ('entry3',), '',
                     DebugConfiguration())
        reg.setDefaultEntry(self.pathPrefix + ('entry1',))
        del reg

        self.checkCommand(self.getSelArgs('entry3') + ['forget'])
        self.checkCommand(self.getSelArgs('entry2') + ['forget'])

        reg = self.getRegistry()
        self.assertEqual(set(reg.getEntryNames(self.pathPrefix)),
                         set(['entry1']))
        descr, config = reg.getEntry(self.pathPrefix + ('entry1',))
        self.assertEqual(config.getParam('bar'), 14)

    def testForgetDefault(self):
        reg = self.getRegistry()
        reg.setEntry(self.pathPrefix + ('entry1',), '',
                     DebugConfiguration(bar=14))
        reg.setEntry(self.pathPrefix + ('entry2',), '',
                     DebugConfiguration())
        reg.setEntry(self.pathPrefix + ('entry3',), '',
                     DebugConfiguration())
        reg.setDefaultEntry(self.pathPrefix + ('entry2',))
        del reg

        self.checkCommandError(self.selPrefix + ['forget'])

    def testForgetInexistent(self):
        self.checkCommandError(self.getSelArgs('entry1') + ['forget'])

    def testForgetExplicit(self):
        self.checkCommandError(self.typePrefix + ['forget'])

    def testNoModelbase(self):
        self.checkCommandError(self.getSelArgs('entry1') + ['forget'])

    def testWithOptions(self):
        self.checkCommandError(self.selPrefix + ['forget', 'someoption'])


class ModelForgetTestCase(ModelTestCase, ForgetTestCase):
    """Test the forget operation at the model level."""

    def testForgetDefault(self):
        pass


class ModelMbDefForgetTestCase(ModelMbDefTestCase, ForgetTestCase):
    """Test the forget operation at the model level, using the
    default modelbase."""
    pass


class SetDefaultTestCase(BasicTestCase):
    """Test the set default operation."""

    def testHelp(self):
        self.checkCommand(['setdefault', '-h'])

    def testSetDefault1(self):
        reg = self.getRegistry()
        reg.setEntry(self.pathPrefix + ('entry1',), '',
                     DebugConfiguration())
        del reg

        stdout = self.checkCommand(self.getSelArgs('entry1') + ['setdefault'])

        self.assertTrue('entry1' in stdout)

        reg = self.getRegistry()
        self.assertEqual(reg.getDefaultName(self.pathPrefix), 'entry1')

    def testSetDefault2(self):
        reg = self.getRegistry()
        reg.setEntry(self.pathPrefix + ('entry1',), '',
                     DebugConfiguration(bar=14))
        reg.setEntry(self.pathPrefix + ('entry2',), '',
                     DebugConfiguration())
        reg.setEntry(self.pathPrefix + ('entry3',), '',
                     DebugConfiguration())
        del reg

        self.checkCommand(self.getSelArgs('entry3') + ['setdefault'])

        reg = self.getRegistry()
        self.assertEqual(reg.getDefaultName(self.pathPrefix), 'entry3')

        self.checkCommand(self.getSelArgs('entry2') + ['setdefault'])

        reg = self.getRegistry()
        self.assertEqual(reg.getDefaultName(self.pathPrefix), 'entry2')

    def testSetDefaultDefault(self):
        reg = self.getRegistry()
        reg.setEntry(self.pathPrefix + ('entry1',), '',
                     DebugConfiguration(bar=14))
        reg.setEntry(self.pathPrefix + ('entry2',), '',
                     DebugConfiguration())
        reg.setEntry(self.pathPrefix + ('entry3',), '',
                     DebugConfiguration())
        reg.setDefaultEntry(self.pathPrefix + ('entry2',))
        del reg

        self.checkCommandError(self.selPrefix + ['setdefault'])

    def testSetDefaultInexistent(self):
        self.checkCommandError(self.getSelArgs('entry1') + ['setdefault'])

    def testSetDefaultExplicit(self):
        self.checkCommandError(self.typePrefix + ['setdefault'])

    def testNoModelbase(self):
        self.checkCommandError(self.getSelArgs('entry1') + ['setdefault'])

    def testWithOptions(self):
        self.checkCommandError(['setdefault', 'someoption'])


class ModelSetDefaultTestCase(ModelTestCase, SetDefaultTestCase):
    """Test the setdefault operation at the model level."""

    def testSetDefaultDefault(self):
        pass


class ModelMbDefSetDefaultTestCase(ModelMbDefTestCase, SetDefaultTestCase):
    """Test the setdefault operation at the model level, using the
    default modelbase."""
    pass


class ImportTestCase(BasicTestCase):
    """Test the import operation."""

    def setUp(self):
        super(ImportTestCase, self).setUp()

        self.selOptions = ['--mbtype=debug', '--modeltype=print']

    def checkPrint(self, cmdLine, checksum):
        stdout = self.checkCommand(['import'] + cmdLine).split('\n')
        stdout.sort()

        m = hashlib.md5()
        for line in stdout:
            m.update(line + '\n')

        self.assertEqual(m.hexdigest(), checksum)

    def testHelp(self):
        self.checkCommand(['import', '-h'])

    def testRdfXML1(self):
        self.checkPrint(['--type=rdfxml', 'data/model1.rdf'],
                        '925d9f176ad033d4e00c68a36b47bbb4')

    # FIXME: Test other parsers.

    def testNoOptions(self):
        self.checkCommandError(['import'])

    def testNoFileType(self):
        self.checkCommandError(['import', 'data/model1.rdf'])

    def testInvalidFileType(self):
        st, out, err = self.checkCommandError(['import', '--type=abcde',
                                               'data/model1.rdf'])
        self.assertTrue('abcde' in err)

    def testFileNotFound1(self):
        st, out, err = self.checkCommandError(['import', '--type=rdfxml',
                                               'xxyyzz/mmnn'])
        self.assertTrue('xxyyzz/mmnn' in err)

    def testFileNotFound2(self):
        st, out, err = self.checkCommandError(['import', '--type=v-modell',
                                               'xxyyzz/mmnn'])
        self.assertTrue('xxyyzz/mmnn' in err)

    def testFileNotFound3(self):
        st, out, err = self.checkCommandError(['import', '--type=xmi',
                                               'xxyyzz/mmnn'])
        self.assertTrue('xxyyzz/mmnn' in err)

    def testFileNotFound4(self):
        st, out, err = self.checkCommandError(['import', '--type=turtle',
                                               'xxyyzz/mmnn'])
        self.assertTrue('xxyyzz/mmnn' in err)

    def testFileNotFound5(self):
        st, out, err = self.checkCommandError(['import', '--type=ntriples',
                                               'xxyyzz/mmnn'])
        self.assertTrue('xxyyzz/mmnn' in err)

