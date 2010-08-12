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


"""Test the forked argparse module include in RelRDF.
"""

import unittest

from relrdf.util import argparse


class ArgparseTestCase(unittest.TestCase):
    """Test cases for the modified argparse module."""

    def setUp(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('--foo', action='store_true')
        self.parser.add_argument('--bar')

    def assertParse(self, parsed, passThrough):
        if parsed != '':
            args = parsed.split(' ')
        else:
            args = []
        if passThrough != '':
            extraArgs = passThrough.split(' ')
        else:
            extraArgs = []
        ns, extras = self.parser.parse_known_args(args + extraArgs,
                                                  contiguous=True)
        self.assertEqual(extras, extraArgs)
        return ns

    def testNoExtras(self):
        ns = self.assertParse('--foo --bar=xx', '')
        self.assertTrue(ns.foo)
        self.assertEqual(ns.bar, 'xx')

    def testCommand1(self):
        ns = self.assertParse('--foo', 'command --bar=xx')
        self.assertTrue(ns.foo)
        self.assertTrue(ns.bar is None)

    def testCommand2(self):
        ns = self.assertParse('--bar=xx', 'command --bar=yy')
        self.assertFalse(ns.foo)
        self.assertEqual(ns.bar, 'xx')

    def testCommand3(self):
        ns = self.assertParse('--bar xx', 'command --bar=yy')
        self.assertFalse(ns.foo)
        self.assertEqual(ns.bar, 'xx')

    def testCommand4(self):
        ns = self.assertParse('', 'command --bar=yy')
        self.assertFalse(ns.foo)
        self.assertTrue(ns.bar is None)

    def testPositionalCommand1(self):
        self.parser.add_argument('baz')
        ns = self.assertParse('--foo yy', 'command --bar=xx')
        self.assertTrue(ns.foo)
        self.assertTrue(ns.bar is None)
        self.assertEqual(ns.baz, 'yy')

    def testPositionalCommand2(self):
        self.parser.add_argument('baz')
        ns = self.assertParse('yy --foo', 'command --bar=xx')
        self.assertTrue(ns.foo)
        self.assertTrue(ns.bar is None)
        self.assertEqual(ns.baz, 'yy')

    def testPositionalCommand3(self):
        self.parser.add_argument('baz')
        ns = self.assertParse('yy --bar=xx', 'command --bar=yy')
        self.assertFalse(ns.foo)
        self.assertEqual(ns.bar, 'xx')
        self.assertEqual(ns.baz, 'yy')

    def testPositionalCommand4(self):
        self.parser.add_argument('baz')
        ns = self.assertParse('yy --bar=xx', 'command --bar=yy')
        self.assertFalse(ns.foo)
        self.assertEqual(ns.bar, 'xx')
        self.assertEqual(ns.baz, 'yy')

    def testPositionalCommand5(self):
        self.parser.add_argument('baz')
        ns = self.assertParse('--bar xx yy', 'command --bar=yy')
        self.assertFalse(ns.foo)
        self.assertEqual(ns.bar, 'xx')
        self.assertEqual(ns.baz, 'yy')

    def testPositionalCommand6(self):
        self.parser.add_argument('baz')
        ns = self.assertParse('yy --bar xx', 'command --bar=yy')
        self.assertFalse(ns.foo)
        self.assertEqual(ns.bar, 'xx')
        self.assertEqual(ns.baz, 'yy')

    def testPositionalCommand7(self):
        self.parser.add_argument('baz')
        ns = self.assertParse('yy', 'command --bar=yy')
        self.assertFalse(ns.foo)
        self.assertTrue(ns.bar is None)
        self.assertEqual(ns.baz, 'yy')

    def testOption1(self):
        ns = self.assertParse('--foo', '--unknown --bar=xx')
        self.assertTrue(ns.foo)
        self.assertTrue(ns.bar is None)

    def testOption2(self):
        ns = self.assertParse('--bar=xx', '--unknown --bar=yy')
        self.assertFalse(ns.foo)
        self.assertEqual(ns.bar, 'xx')

    def testOption3(self):
        ns = self.assertParse('--bar xx', '--unknown --bar=yy')
        self.assertFalse(ns.foo)
        self.assertEqual(ns.bar, 'xx')

    def testOption4(self):
        ns = self.assertParse('', '--unknown --bar=yy')
        self.assertFalse(ns.foo)
        self.assertTrue(ns.bar is None)

    def testPositionalOption1(self):
        self.parser.add_argument('baz')
        ns = self.assertParse('--foo yy', '--unknown --bar=xx')
        self.assertTrue(ns.foo)
        self.assertTrue(ns.bar is None)
        self.assertEqual(ns.baz, 'yy')

    def testPositionalOption2(self):
        self.parser.add_argument('baz')
        ns = self.assertParse('yy --foo', '--unknown --bar=xx')
        self.assertTrue(ns.foo)
        self.assertTrue(ns.bar is None)
        self.assertEqual(ns.baz, 'yy')

    def testPositionalOption3(self):
        self.parser.add_argument('baz')
        ns = self.assertParse('yy --bar=xx', '--unknown --bar=yy')
        self.assertFalse(ns.foo)
        self.assertEqual(ns.bar, 'xx')
        self.assertEqual(ns.baz, 'yy')

    def testPositionalOption4(self):
        self.parser.add_argument('baz')
        ns = self.assertParse('yy --bar=xx', '--unknown --bar=yy')
        self.assertFalse(ns.foo)
        self.assertEqual(ns.bar, 'xx')
        self.assertEqual(ns.baz, 'yy')

    def testPositionalOption5(self):
        self.parser.add_argument('baz')
        ns = self.assertParse('--bar xx yy', '--unknown --bar=yy')
        self.assertFalse(ns.foo)
        self.assertEqual(ns.bar, 'xx')
        self.assertEqual(ns.baz, 'yy')

    def testPositionalOption6(self):
        self.parser.add_argument('baz')
        ns = self.assertParse('yy --bar xx', '--unknown --bar=yy')
        self.assertFalse(ns.foo)
        self.assertEqual(ns.bar, 'xx')
        self.assertEqual(ns.baz, 'yy')

    def testPositionalOption7(self):
        self.parser.add_argument('baz')
        ns = self.assertParse('yy', '--unknown --bar=yy')
        self.assertFalse(ns.foo)
        self.assertTrue(ns.bar is None)
        self.assertEqual(ns.baz, 'yy')
