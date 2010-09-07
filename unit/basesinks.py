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


"""Test RelRDF's base model sinks, currently associated to the debug
modelbase.
"""

import unittest

import relrdf
from relrdf import Uri, Namespace, Literal

from common import raises


class TestCase(unittest.TestCase):
    """Test case for the basic sinks."""

    def setUp(self):
        self.mb = relrdf.getModelbaseFromParams('debug')
        ex = Namespace('http://example.com/')
        self.stmts = [
            (ex.c, ex.p1, ex.d),
            (ex.c, ex.p2, Literal('x')),
            (ex.a, ex.p1, ex.c),
            (ex.a, ex.p1, ex.d),
            (ex.d, ex.p2, Literal(3)),
            ]

    def testNullSink(self):
        sink = self.mb.getSinkFromParams('null')
        for stmt in self.stmts:
            sink.triple(*stmt)

    def testListSink(self):
        sink = self.mb.getSinkFromParams('list')
        for stmt in self.stmts:
            sink.triple(*stmt)
        self.assertEqual(self.stmts, sink)

    def xtestDictSink(self):
        # FIXME: The sink must be corrected for this to work.
        sink = self.mb.getSinkFromParams('dict')
        for stmt in self.stmts:
            sink.triple(*stmt)
        self.assertEqual(sorted(self.stmts),
                         sorted([(s, p, o) for (s, p), o
                                 in sink.iteritems()]))
