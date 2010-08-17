# -*- coding: utf-8 -*-
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


"""Common definitions for the V-Modell schema."""

import relrdf
from relrdf import commonns
from relrdf.expression import uri

from relrdf.presentation import graph


vmxt = uri.Namespace('http://www.v-modell-xt.de/schema/1#')
vmxti = uri.Namespace('http://www.v-modell-xt.de/model/1#')


@graph.transf(inputProps=('label', 'newLabel', 'oldLabel'),
              outputProps=('label',))
def _createCompLabel(props):
    if props['label'] is not None:
        pass
    elif props['newLabel'] is None:
        props['label'] = props['oldLabel']
    elif props['oldLabel'] is None:
        props['label'] = props['newLabel']
    else:
        props['label'] = '<span foreground="red">%s</span> -> ' \
                         '<span foreground="green">%s</span>' % \
                         (props['oldLabel'], props['newLabel'])

@graph.transf(inputProps=('type', 'label'),
              outputProps=('label',))
def _addTypeToLabel(props):
    # Use the URI if the name is not found in the table.
    typeName = _typeNames.get(props['type'],
                              props['type'][len(vmxt):])
    props['label'] = "<b>%s:</b> %s" % (typeName, props['label'])


_compColorMap = {
    commonns.relrdf.compA: 'red',
    commonns.relrdf.compAB: 'black',
    commonns.relrdf.compB: 'green',
}

_compFillColorMap = {
    commonns.relrdf.compA: '#FFE0E0',
    commonns.relrdf.compAB: 'white',
    commonns.relrdf.compB: '#E0FFE0',
}

@graph.transf(inputProps=('comp',),
              outputProps=('color', 'fillColor'))
def _colorsFromComp(props):
    props['color'] = _compColorMap[props['comp']]
    props['fillColor'] = _compFillColorMap[props['comp']]


class VModellGraphMaker(graph.RdfGraphvizMaker):
    __slots__ = ('transfFuncs',)

    transfFuncs = (_createCompLabel,
                   _addTypeToLabel,
                   _colorsFromComp,
                   )

    def addResults(self, results):
        # Wrap the results in a transformer.
        results = graph.PropertyTransformer(results, self.transfFuncs)
        super(VModellGraphMaker, self).addResults(results)

