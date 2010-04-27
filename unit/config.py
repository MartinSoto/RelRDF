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


"""Test RelRDF's modelbase configuration facilities.
"""

import unittest
import os, tempfile, shutil

from relrdf.error import ConfigurationError
from relrdf import config

from common import raises


class BasicTestCase(unittest.TestCase):
    """Basic test case for the modelbase registry."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.create()
        self.init()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def create(self):
        """Discard the current registry object (if any) and make a new
        one for the same file."""
        self.reg = config.ModelbaseRegistry(os.path.join(self.dir,
                                                         'registry.json'))

    def init(self):
        """Add entries to the registry as necessary."""
        pass

    def maybeReopen(self):
        """Discard the current registry and open a new one. This
        method can be redefined to make it a no-op, so that the same
        set of test cases runs on a single object."""
        self.create()


class CreationTestCase(BasicTestCase):
    """Registry creation."""

    def testJustCreate(self):
        pass

    def testStoreEntry(self):
        entry = ('backend1', 1, 'descr1',
                 {'field1': 'A', 'field2': 5})
        self.reg.setRawEntry('entry1', *entry)
        self.maybeReopen()
        self.assertEqual(self.reg.getRawEntry('entry1'), entry)

    def testNames(self):
        entry = ('backend1', 1, 'descr1',
                 {'field1': 'A', 'field2': 5})

        self.assertEqual(len(list(self.reg.getEntryNames())), 0)
        self.reg.setRawEntry('entry1', *entry)
        self.maybeReopen()

        names = list(self.reg.getEntryNames())
        self.assertEqual(len(names), 1)
        self.assertTrue('entry1' in names)

        self.reg.setRawEntry('entry2', *entry)
        self.maybeReopen()

        names = list(self.reg.getEntryNames())
        self.assertEqual(len(names), 2)
        self.assertTrue('entry1' in names)
        self.assertTrue('entry2' in names)

    def testNoDefault1(self):
        self.assertTrue(self.reg.getDefaultName() is None)

    def testNoDefault2(self):
        entry = ('backend1', 1, 'descr1',
                 {'field1': 'A', 'field2': 5})
        self.reg.setRawEntry('entry1', *entry)
        self.maybeReopen()
        self.assertTrue(self.reg.getDefaultName() is None)


class CreationTestCaseNoReopen(CreationTestCase):
    """Registry creation, no reopen."""

    def maybeReopen(self):
        pass


class MultientryTestCase(BasicTestCase):
    """Element deletion."""

    def init(self):
        # Insert three entries:

        self.entry1 = ('backend1', 1, 'descr1',
                       {'field1': 'A', 'field2': 5})
        self.entry2 = ('backend2', 1, 'descr2',
                       {'field3': 'B',})
        self.entry3 = ('backend1', 1, 'descr3',
                       {'field1': 'C', 'field2': 5, 'field3': [1, 2]})
        self.entry4 = ('backend2', 1, 'descr4',
                       {'field3': 'D'})

        self.reg.setRawEntry('entry1', *self.entry1)
        self.reg.setRawEntry('entry2', *self.entry2)
        self.reg.setRawEntry('entry3', *self.entry3)

    def testNoRemove(self):
        self.maybeReopen()

        names = list(self.reg.getEntryNames())
        self.assertEqual(len(names), 3)
        self.assertEqual(self.reg.getRawEntry('entry1'), self.entry1)
        self.assertEqual(self.reg.getRawEntry('entry2'), self.entry2)
        self.assertEqual(self.reg.getRawEntry('entry3'), self.entry3)

    def testRemove1(self):
        self.reg.removeEntry('entry2')
        self.maybeReopen()

        names = list(self.reg.getEntryNames())
        self.assertEqual(len(names), 2)
        self.assertEqual(self.reg.getRawEntry('entry1'), self.entry1)
        self.assertEqual(self.reg.getRawEntry('entry3'), self.entry3)

    def testRemove2(self):
        self.reg.removeEntry('entry1')
        self.reg.removeEntry('entry3')
        self.maybeReopen()

        names = list(self.reg.getEntryNames())
        self.assertEqual(len(names), 1)
        self.assertEqual(self.reg.getRawEntry('entry2'), self.entry2)

    def testRemoveAll(self):
        self.reg.removeEntry('entry1')
        self.reg.removeEntry('entry2')
        self.reg.removeEntry('entry3')
        self.maybeReopen()

        names = list(self.reg.getEntryNames())
        self.assertEqual(len(names), 0)

    def testNoRemoveAdd(self):
        self.reg.setRawEntry('entry4', *self.entry4)
        self.maybeReopen()

        names = list(self.reg.getEntryNames())
        self.assertEqual(len(names), 4)
        self.assertEqual(self.reg.getRawEntry('entry1'), self.entry1)
        self.assertEqual(self.reg.getRawEntry('entry2'), self.entry2)
        self.assertEqual(self.reg.getRawEntry('entry3'), self.entry3)
        self.assertEqual(self.reg.getRawEntry('entry4'), self.entry4)

    def testRemove1Add(self):
        self.reg.removeEntry('entry2')
        self.reg.setRawEntry('entry4', *self.entry4)
        self.maybeReopen()

        names = list(self.reg.getEntryNames())
        self.assertEqual(len(names), 3)
        self.assertEqual(self.reg.getRawEntry('entry1'), self.entry1)
        self.assertEqual(self.reg.getRawEntry('entry3'), self.entry3)
        self.assertEqual(self.reg.getRawEntry('entry4'), self.entry4)

    def testRemove2Add(self):
        self.reg.removeEntry('entry1')
        self.reg.removeEntry('entry3')
        self.reg.setRawEntry('entry4', *self.entry4)
        self.maybeReopen()

        names = list(self.reg.getEntryNames())
        self.assertEqual(len(names), 2)
        self.assertEqual(self.reg.getRawEntry('entry2'), self.entry2)
        self.assertEqual(self.reg.getRawEntry('entry4'), self.entry4)

    def testRemoveAllAdd(self):
        self.reg.removeEntry('entry1')
        self.reg.removeEntry('entry2')
        self.reg.removeEntry('entry3')
        self.reg.setRawEntry('entry4', *self.entry4)
        self.maybeReopen()

        names = list(self.reg.getEntryNames())
        self.assertEqual(len(names), 1)
        self.assertEqual(self.reg.getRawEntry('entry4'), self.entry4)

    @raises(ConfigurationError)
    def testGetInexistent(self):
        self.maybeReopen()
        self.reg.getRawEntry('entry5')

    @raises(ConfigurationError)
    def testGetRemoved(self):
        self.reg.removeEntry('entry2')
        self.maybeReopen()
        self.reg.getRawEntry('entry2')

    @raises(ConfigurationError)
    def testRemoveInexistent(self):
        self.maybeReopen()
        self.reg.removeEntry('entry5')

    @raises(ConfigurationError)
    def testRemoveRemoved(self):
        self.reg.removeEntry('entry2')
        self.maybeReopen()
        self.reg.removeEntry('entry2')

    def testGetDefaultNameUnset(self):
        self.maybeReopen()
        self.assertTrue(self.reg.getDefaultName() is None)

    @raises(ConfigurationError)
    def testGetDefaultUnset(self):
        self.maybeReopen()
        self.reg.getRawEntry()

    def testGetDefaultName(self):
        self.reg.setDefaultEntry('entry2')
        self.maybeReopen()
        self.assertEqual(self.reg.getDefaultName(), 'entry2')

    def testGetDefault(self):
        self.reg.setDefaultEntry('entry2')
        self.maybeReopen()
        self.assertEqual(self.reg.getDefaultName(), 'entry2')

    @raises(ConfigurationError)
    def testSetDefaultInexistent(self):
        self.reg.setDefaultEntry('entry4')

    def testRemoveDefaultEntry(self):
        self.reg.setDefaultEntry('entry2')
        self.reg.removeEntry('entry2')
        self.maybeReopen()
        self.assertTrue(self.reg.getDefaultName() is None)


class MultientryTestCaseNoReopen(MultientryTestCase):
    """Element deletion, no reopen."""

    def maybeReopen(self):
        pass


class FileLocationTestCase(unittest.TestCase):
    """Automatic file selection."""

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

    def tearDown(self):
        shutil.rmtree(self.dir)

    def create(self):
        """Create a registry object and add an entry to it."""
        self.reg = config.ModelbaseRegistry()
        entry = ('backend1', 1, 'descr1',
                 {'field1': 'A', 'field2': 5})
        self.reg.setRawEntry('entry1', *entry)

    @raises(ConfigurationError)
    def testNoEnv(self):
        self.create()

    def testHome(self):
        os.environ['HOME'] = self.dir
        self.create()
        self.assertTrue(os.path.exists(os.path.join(self.dir,
                                                    '.config',
                                                    config.ModelbaseRegistry.\
                                                        DEFAULT_REGISTRY_NAME)))

    def testXdg(self):
        os.environ['XDG_DATA_HOME'] = os.path.join(self.dir, 'config')
        self.create()
        self.assertTrue(os.path.exists(os.path.join(self.dir,
                                                    'config',
                                                    config.ModelbaseRegistry.\
                                                        DEFAULT_REGISTRY_NAME)))

    def testConf(self):
        os.environ['RELRDF_CONFIG'] = os.path.join(self.dir, 'xxx', 'theConf')
        self.create()
        self.assertTrue(os.path.exists(os.path.join(self.dir, 'xxx',
                                                    'theConf')))

    def testPermissions(self):
        os.environ['HOME'] = self.dir
        self.create()
        self.assertEqual(os.stat(self.reg.getFileName()).st_mode & 0177, 0)
