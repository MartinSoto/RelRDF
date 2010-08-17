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
compUnmodif = commonns.relrdf.compAB
compOld = commonns.relrdf.compA
compNew = commonns.relrdf.compB

def propCompValues(valueSubgraph):
    unmodif = None
    old = None
    new = None

    for value, comp in valueSubgraph:
        if comp == compOld:
            old = value
        elif comp == compNew:
            new = value
        else:
            unmodif = value

    return (unmodif, old, new)


class TwoWayTextValueDisplay(generators.StdTextValueDisplay):
    __slots__ = ()

    def _protectText(self, text):
        return unicode(genshi.escape(text))

    def formatValue(self, valueSubgraph):
        (unmodif, old, new) = propCompValues(valueSubgraph)

        if unmodif is not None:
            res = '<span class="compUnmodif">%s</span>' % \
                self._protectText(unmodif)
        elif old is None and new is None:
            res = '<span class="compError">###</span>'
        elif new is None:
            res = '<span class="compOld">%s</span>' % \
                self._protectText(old)
        elif old is None:
            res = '<span class="compNew">%s</span>' % \
                self._protectText(new)
        else:
            try:
                res = '<span>%s</span>' % \
                    xmlcomp.compare(self._protectText(old),
                                    self._protectText(new))
            except:
                print >> sys.stderr, '*** Failed comparing:'
                print >> sys.stderr, '*** old:', old
                print >> sys.stderr, '*** new:', new

                res = '<span class="compOld">%s</span>' \
                    '<span class="compNew">%s</span>' % \
                    (self._protectText(old),
                     self._protectText(new))

        try:
            return genshi.XML(res)
        except:
            print >> sys.stderr, '*** Failed formatting:', res
            print >> sys.stderr, '*** Unmodif:', unmodif
            print >> sys.stderr, '*** old:', old
            print >> sys.stderr, '*** new:', new
            raise


class TwoWayHtmlValueDisplay(generators.StdHtmlValueDisplay):
    __slots__ = ()

    def formatValue(self, valueSubgraph):
        (unmodif, old, new) = \
            propCompValues(valueSubgraph)

        if unmodif is not None:
            res = '<div class="compUnmodif">%s</div>' % unmodif
        elif old is None and new is None:
            res = '<div class="compError">###</div>'
        elif new is None:
            res = '<div class="compOld">%s</div>' % old
        elif old is None:
            res = '<div class="compNew">%s</div>' % new
        else:
            try:
                res = '<div>%s</div>' % xmlcomp.compare(old, new)
            except:
                print >> sys.stderr, '*** Failed comparing:'
                print >> sys.stderr, '*** old:', old.encode('utf8')
                print >> sys.stderr, '*** new:', new.encode('utf8')

                res = '<div><div class="compOld">%s</div>' \
                    '<div class="compNew">%s</div></div>' % (old, new)

        try:
            return self.prepareHtml(res)
        except:
            print >> sys.stderr, '*** Failed formatting:', res
            print >> sys.stderr, '*** Unmodif:', unmodif.encode('utf8')
            print >> sys.stderr, '*** old:', old.encode('utf8')
            print >> sys.stderr, '*** new:', new.encode('utf8')
            raise


class TwoWayRdfResList(generators.StdRdfResList):
    __slots__ = ()

    def refClass(self, res, graph):
        if graph == compOld:
            return 'resRefOld'
        elif graph == compNew:
            return 'resRefNew'
        else:
            return 'resRef'

