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

import sys

import genshi

from relrdf import commonns

from relrdf.presentation import xmlcomp, docgen

import generators


# Cache the URIs.
compA = commonns.relrdf.compA
compB = commonns.relrdf.compB
compC = commonns.relrdf.compC
compAB = commonns.relrdf.compAB
compAC = commonns.relrdf.compAC
compBC = commonns.relrdf.compBC
compABC = commonns.relrdf.compABC


def compValues(valueSubgraph):
    valueSubgraph = list(valueSubgraph)
    valueA = ''
    valueB = ''
    valueC = ''

    for value, comp in valueSubgraph:
        if comp == compA:
            valueA = value
            cssCls = 'compDeletedBC'
        elif comp == compB:
            valueB = value
            cssCls = 'compAddedB'
        elif comp == compC:
            valueC = value
            cssCls = 'compAddedC'
        elif comp == compAB:
            valueA = value
            valueB = value
            cssCls = 'compDeletedC'
        elif comp == compAC:
            valueA = value
            valueC = value
            cssCls = 'compDeletedB'
        elif comp == compBC:
            valueB = value
            valueC = value
            cssCls = 'compAddedBC'
        elif comp == compABC:
            valueA = value
            valueB = value
            valueC = value
            cssCls = 'compUnmodif'
        else:
            cssCls = 'compUnmodif'

    return (valueA, valueB, valueC)


class ThreeWayTextValueDisplay(generators.StdTextValueDisplay):
    __slots__ = ()

    def _escape(self, text):
        return unicode(genshi.escape(text))

    def formatValue(self, valueSubgraph):
        result = compValues(valueSubgraph)

        valueA, valueB, valueC = result
        try:
            comp = xmlcomp.compare3(self._escape(valueA),
                                    self._escape(valueB),
                                    self._escape(valueC))
            res = '''
              <span class="compValueC">%s</span>''' % comp
                
        except:
            print >> sys.stderr, '*** Failed comparing:'

            res = '<span><span class="compDeletedBC">%s</span>' \
                '<span class="compAddedB">%s</span>' \
                '<span class="compAddedC">%s</span></span>' % \
                (self._escape(valueA), self._escape(valueB),
                 self._escape(valueC))

            print >> sys.stderr, '*** valueA:', valueA.encode('utf-8')
            print >> sys.stderr, '*** valueB:', valueB.encode('utf-8')
            print >> sys.stderr, '*** valueC:', valueC.encode('utf-8')

        try:
            return genshi.XML(res)
        except:
            print >> sys.stderr, '*** Failed formatting:', res.encode('utf-8')


class ThreeWayHtmlValueDisplay(generators.StdHtmlValueDisplay):
    __slots__ = ()

    def formatValue(self, valueSubgraph):
        result = compValues(valueSubgraph)

        try:
            comp = xmlcomp.compare3(*result)
            res = '''
              <table>
                <tr>
                  <td class="compValueB">%s</td>
	          <td class="compValueC">%s</td>
                </tr>
              </table>''' % (comp, comp)
        except:
            print >> sys.stderr, '*** Failed comparing:'

            res = '<div><div class="compDeletedBC">%s</div>' \
                '<div class="compAddedB">%s</div>' \
                '<div class="compAddedC">%s</div></div>' % result

            valueA, valueB, valueC = result
            print >> sys.stderr, '*** valueA:', valueA.encode('utf-8')
            print >> sys.stderr, '*** valueB:', valueB.encode('utf-8')
            print >> sys.stderr, '*** valueC:', valueC.encode('utf-8')

        try:
            return self.prepareHtml(res)
        except:
            print >> sys.stderr, '*** Failed formatting:', res.encode('utf-8')


class ThreeWayRdfResList(generators.StdRdfResList):
    __slots__ = ()

    graphToCss = {
        compA: 'resRefDeletedBC',
        compB: 'resRefAddedB',
        compC: 'resRefAddedC',
        compAB: 'resRefDeletedC',
        compAC: 'resRefDeletedB',
        compBC: 'resRefAddedBC',
        compABC: 'resRef',
        }

    def refClass(self, res, graph):
        return self.graphToCss[graph]
