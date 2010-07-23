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
from relrdf.debug import DebugConfiguration

from common import raises


class BasicTestCase(unittest.TestCase):
    """Basic test case for the configuration registry."""

    def __init__(self, *args, **kwargs):
        super(BasicTestCase, self).__init__(*args, **kwargs)
        self.basePath = ()

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.create()
        self.init()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def create(self):
        """Discard the current registry object (if any) and make a new
        one for the same file."""
        self.reg = config.Registry(os.path.join(self.dir,
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
        self.reg.setRawEntry(self.basePath + ('entry1',), *entry)
        self.maybeReopen()
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry1',)),
                         entry)

    def testNames(self):
        entry = ('backend1', 1, 'descr1',
                 {'field1': 'A', 'field2': 5})

        self.assertEqual(len(list(self.reg.getEntryNames(self.basePath))), 0)
        self.reg.setRawEntry(self.basePath + ('entry1',), *entry)
        self.maybeReopen()

        names = list(self.reg.getEntryNames(self.basePath))
        self.assertEqual(len(names), 1)
        self.assertTrue('entry1' in names)

        self.reg.setRawEntry(self.basePath + ('entry2',), *entry)
        self.maybeReopen()

        names = list(self.reg.getEntryNames(self.basePath))
        self.assertEqual(len(names), 2)
        self.assertTrue('entry1' in names)
        self.assertTrue('entry2' in names)

    def testNoDefault1(self):
        self.assertTrue(self.reg.getDefaultName(self.basePath) is None)

    def testNoDefault2(self):
        entry = ('backend1', 1, 'descr1',
                 {'field1': 'A', 'field2': 5})
        self.reg.setRawEntry(self.basePath + ('entry1',), *entry)
        self.maybeReopen()
        self.assertTrue(self.reg.getDefaultName(self.basePath) is None)


class CreationTestCaseNoReopen(CreationTestCase):
    """Registry creation, no reopen."""

    def maybeReopen(self):
        pass


class CreationTestCaseSubentry(CreationTestCase):
    """Registry creation, test subentries."""

    def __init__(self, *args, **kwargs):
        super(CreationTestCaseSubentry, self).__init__(*args, **kwargs)
        self.basePath = ('entry1',)

    def init(self):
        # Insert three entries:

        self.entry1 = ('backend1', 1, 'descr1',
                       {'field1': 'A', 'field2': 5})
        self.entry2 = ('backend2', 1, 'descr2',
                       {'field3': 'B',})
        self.entry3 = ('backend1', 1, 'descr3',
                       {'field1': 'C', 'field2': 5, 'field3': [1, 2]})

        self.reg.setRawEntry(('entry1',), *self.entry1)    
        self.reg.setRawEntry(('entry2',), *self.entry2)
        self.reg.setRawEntry(('entry3',), *self.entry3)


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

        self.reg.setRawEntry(self.basePath + ('entry1',), *self.entry1)
        self.reg.setRawEntry(self.basePath + ('entry2',), *self.entry2)
        self.reg.setRawEntry(self.basePath + ('entry3',), *self.entry3)

    def testNoRemove(self):
        self.maybeReopen()

        names = list(self.reg.getEntryNames(self.basePath))
        self.assertEqual(len(names), 3)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry1',)),
                         self.entry1)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry2',)),
                         self.entry2)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry3',)),
                         self.entry3)

    def testRemove1(self):
        self.reg.removeEntry(self.basePath + ('entry2',))
        self.maybeReopen()

        names = list(self.reg.getEntryNames(self.basePath))
        self.assertEqual(len(names), 2)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry1',)),
                         self.entry1)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry3',)),
                         self.entry3)

    def testRemove2(self):
        self.reg.removeEntry(self.basePath + ('entry1',))
        self.reg.removeEntry(self.basePath + ('entry3',))
        self.maybeReopen()

        names = list(self.reg.getEntryNames(self.basePath))
        self.assertEqual(len(names), 1)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry2',)),
                         self.entry2)

    def testRemoveAll(self):
        self.reg.removeEntry(self.basePath + ('entry1',))
        self.reg.removeEntry(self.basePath + ('entry2',))
        self.reg.removeEntry(self.basePath + ('entry3',))
        self.maybeReopen()

        names = list(self.reg.getEntryNames(self.basePath))
        self.assertEqual(len(names), 0)

    def testNoRemoveAdd(self):
        self.reg.setRawEntry(self.basePath + ('entry4',), *self.entry4)
        self.maybeReopen()

        names = list(self.reg.getEntryNames(self.basePath))
        self.assertEqual(len(names), 4)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry1',)),
                         self.entry1)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry2',)),
                         self.entry2)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry3',)),
                         self.entry3)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry4',)),
                         self.entry4)

    def testRemove1Add(self):
        self.reg.removeEntry(self.basePath + ('entry2',))
        self.reg.setRawEntry(self.basePath + ('entry4',), *self.entry4)
        self.maybeReopen()

        names = list(self.reg.getEntryNames(self.basePath))
        self.assertEqual(len(names), 3)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry1',)),
                         self.entry1)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry3',)),
                         self.entry3)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry4',)),
                         self.entry4)

    def testRemove2Add(self):
        self.reg.removeEntry(self.basePath + ('entry1',))
        self.reg.removeEntry(self.basePath + ('entry3',))
        self.reg.setRawEntry(self.basePath + ('entry4',), *self.entry4)
        self.maybeReopen()

        names = list(self.reg.getEntryNames(self.basePath))
        self.assertEqual(len(names), 2)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry2',)),
                         self.entry2)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry4',)),
                         self.entry4)

    def testRemoveAllAdd(self):
        self.reg.removeEntry(self.basePath + ('entry1',))
        self.reg.removeEntry(self.basePath + ('entry2',))
        self.reg.removeEntry(self.basePath + ('entry3',))
        self.reg.setRawEntry(self.basePath + ('entry4',), *self.entry4)
        self.maybeReopen()

        names = list(self.reg.getEntryNames(self.basePath))
        self.assertEqual(len(names), 1)
        self.assertEqual(self.reg.getRawEntry(self.basePath + ('entry4',)),
                         self.entry4)

    @raises(ConfigurationError)
    def testGetInexistent(self):
        self.maybeReopen()
        self.reg.getRawEntry(self.basePath + ('entry5',))

    @raises(ConfigurationError)
    def testGetRemoved(self):
        self.reg.removeEntry(self.basePath + ('entry2',))
        self.maybeReopen()
        self.reg.getRawEntry(self.basePath + ('entry2',))

    @raises(ConfigurationError)
    def testRemoveInexistent(self):
        self.maybeReopen()
        self.reg.removeEntry(self.basePath + ('entry5',))

    @raises(ConfigurationError)
    def testRemoveRemoved(self):
        self.reg.removeEntry(self.basePath + ('entry2',))
        self.maybeReopen()
        self.reg.removeEntry(self.basePath + ('entry2',))

    def testGetDefaultNameUnset(self):
        self.maybeReopen()
        self.assertTrue(self.reg.getDefaultName(self.basePath) is None)

    @raises(ConfigurationError)
    def testGetDefaultUnset(self):
        self.maybeReopen()
        self.reg.getRawEntry(self.basePath + (None,))

    def testGetDefaultName(self):
        self.reg.setDefaultEntry(self.basePath + ('entry2',))
        self.maybeReopen()
        self.assertEqual(self.reg.getDefaultName(self.basePath), 'entry2')

    def testGetDefault(self):
        self.reg.setDefaultEntry(self.basePath + ('entry2',))
        self.maybeReopen()
        self.assertEqual(self.reg.getDefaultName(self.basePath), 'entry2')

    @raises(ConfigurationError)
    def testSetDefaultInexistent(self):
        self.reg.setDefaultEntry(self.basePath + ('entry4',))

    def testRemoveDefaultEntry(self):
        self.reg.setDefaultEntry(self.basePath + ('entry2',))
        self.reg.removeEntry(self.basePath + ('entry2',))
        self.maybeReopen()
        self.assertTrue(self.reg.getDefaultName(self.basePath) is None)


class MultientryTestCaseNoReopen(MultientryTestCase):
    """Element deletion, no reopen."""

    def maybeReopen(self):
        pass


class MultientryTestCaseSubentry(MultientryTestCase):
    """Entry deletion, test subentries."""

    def __init__(self, *args, **kwargs):
        super(MultientryTestCaseSubentry, self).__init__(*args, **kwargs)
        self.basePath = ('entry1',)

    def init(self):
        # Insert three entries:

        self.entry1 = ('backend1', 1, 'descr1',
                       {'field1': 'A', 'field2': 5})
        self.entry2 = ('backend2', 1, 'descr2',
                       {'field3': 'B',})
        self.entry3 = ('backend1', 1, 'descr3',
                       {'field1': 'C', 'field2': 5, 'field3': [1, 2]})

        self.reg.setRawEntry(('entry1',), *self.entry1)    
        self.reg.setRawEntry(('entry2',), *self.entry2)
        self.reg.setRawEntry(('entry3',), *self.entry3)

        super(MultientryTestCaseSubentry, self).init()


class MultientryTestCaseWithSubentries(MultientryTestCase):
    """Entry deletion, top level but subentries present."""

    def init(self):
        # Insert three entries and three subentries:

        self.entry1 = ('backend1', 1, 'descr1',
                       {'field1': 'A', 'field2': 5})
        self.entry2 = ('backend2', 1, 'descr2',
                       {'field3': 'B',})
        self.entry3 = ('backend1', 1, 'descr3',
                       {'field1': 'C', 'field2': 5, 'field3': [1, 2]})
        self.entry4 = ('backend2', 1, 'descr4',
                       {'field3': 'D'})

        self.sub1 = ('backend3', 2, 'descr4',
                     {'field6': 'XX', 'field7': 'YY'})
        self.sub2 = ('backend3', 2, 'descr5',
                     {'field6': 'ZZ', 'field7': 'WW'})
        self.sub3 = ('backend4', 1, 'descr6',
                     {'field6': 'KK', 'field7': 'QQ'})

        self.reg.setRawEntry(('entry1',), *self.entry1)    
        self.reg.setRawEntry(('entry2',), *self.entry2)
        self.reg.setRawEntry(('entry3',), *self.entry3)

        self.reg.setRawEntry(('entry2', 'sub1'), *self.sub1)
        self.reg.setRawEntry(('entry3', 'sub2'), *self.sub2)
        self.reg.setRawEntry(('entry3', 'sub3'), *self.sub3)

    def tearDown(self):
        try:
            entry1 = self.reg.getRawEntry(('entry1',))
        except ConfigurationError:
            entry1 = None
        try:
            entry2 = self.reg.getRawEntry(('entry2',))
        except ConfigurationError:
            entry2 = None
        try:
            entry3 = self.reg.getRawEntry(('entry3',))
        except ConfigurationError:
            entry3 = None

        if entry1 is not None:
            self.assertEqual(len(list(self.reg.getEntryNames(('entry1',)))), 0)
        if entry2 is not None:
            self.assertEqual(len(list(self.reg.getEntryNames(('entry2',)))), 1)
            self.assertEqual(self.reg.getRawEntry(('entry2', 'sub1')),
                             self.sub1)
        if entry3 is not None:
            self.assertEqual(len(list(self.reg.getEntryNames(('entry3',)))), 2)
            self.assertEqual(self.reg.getRawEntry(('entry3', 'sub2')),
                             self.sub2)
            self.assertEqual(self.reg.getRawEntry(('entry3', 'sub3')),
                             self.sub3)

        super(MultientryTestCaseWithSubentries, self).tearDown()


class MultientryTestCaseDefaultSubentry(MultientryTestCase):
    """Registry creation, test subentries."""

    def __init__(self, *args, **kwargs):
        super(MultientryTestCaseDefaultSubentry, self).__init__(*args, **kwargs)
        self.basePath = (None,)

    def init(self):
        # Insert three entries:

        self.entry1 = ('backend1', 1, 'descr1',
                       {'field1': 'A', 'field2': 5})
        self.entry2 = ('backend2', 1, 'descr2',
                       {'field3': 'B',})
        self.entry3 = ('backend1', 1, 'descr3',
                       {'field1': 'C', 'field2': 5, 'field3': [1, 2]})

        self.reg.setRawEntry(('entry1',), *self.entry1)    
        self.reg.setRawEntry(('entry2',), *self.entry2)
        self.reg.setRawEntry(('entry3',), *self.entry3)

        # Set entry2 as default.
        self.reg.setDefaultEntry(('entry2',))

        super(MultientryTestCaseDefaultSubentry, self).init()


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
        self.reg = config.Registry()
        entry = ('backend1', 1, 'descr1',
                 {'field1': 'A', 'field2': 5})
        self.reg.setRawEntry(('entry1',), *entry)

    @raises(ConfigurationError)
    def testNoEnv(self):
        self.create()

    def testHome(self):
        os.environ['HOME'] = self.dir
        self.create()
        self.assertTrue(os.path.exists(os.path.join(self.dir,
                                                    '.config',
                                                    config.Registry.\
                                                        DEFAULT_REGISTRY_NAME)))

    def testXdg(self):
        os.environ['XDG_DATA_HOME'] = os.path.join(self.dir, 'config')
        self.create()
        self.assertTrue(os.path.exists(os.path.join(self.dir,
                                                    'config',
                                                    config.Registry.\
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


class ConfigObjectTestCase(BasicTestCase):
    """Test the methods dealing with configuration objects."""

    # If we were doing pure black-box testing, we would have to repeat
    # everything we did for the raw case here. This should suffice for
    # the moment, though.

    def init(self):
        self.config = DebugConfiguration(foo='theFoo', bar=42, baz=True)

    def testStoreRetrieve(self):
        path = self.basePath + ('entry1',)
        descr = 'The description'
        self.reg.setEntry(path, descr, self.config)
        self.maybeReopen()
        descr2, config = self.reg.getEntry(path)

        self.assertEqual(descr2, descr)
        self.assertEqual(self.config.getParams(), config.getParams())


class ConfigObjectTestCaseNoReopen(ConfigObjectTestCase):
    """Test the methods dealing with configuration objects, no reopen."""

    def maybeReopen(self):
        pass

