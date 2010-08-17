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

import genshi

from relrdf import commonns

from relrdf.presentation import docgen


class Placeholder(docgen.Template):
    __slots__ = ('text')

    arguments = ()

    def __init__(self, text='PLACEHOLDER'):
        self.text = text

    templateVrt = docgen.parseTemplate('''
      <p style="background: red; color: white;">${self.text}</p>
      ''')

    templateHrz = docgen.parseTemplate('''
      <span style="background: red; color: white;">${self.text}</span>
      ''')


class MainPageDisplay(docgen.Template):
    __slots__ = ()

    arguments = ('makeTitle',)

    templateVrt = docgen.loadTemplate('index.genshi')


class ResourcePageDisplay(docgen.Template):
    __slots__ = ()

    arguments = ('res',

                 'resourceDsp',)

    templateVrt = docgen.loadTemplate('respage.genshi')


class ResourceDisplay(docgen.Template):
    __slots__ = ()

    arguments = ('res',

                 'resTypeDsp',
                 'resNameDsp',
                 'textPropDsp',
                 'htmlPropDsp',
                 'ogRelPropDsp',
                 'icRelPropDsp',

                 'vmxt',)

    templateVrt = docgen.loadTemplate('resource.genshi')


class OgPropertyDisplay(docgen.Template):
    __slots__ = ()

    arguments = ('model',
                 'res',
                 'prop',
                 'ogRelNames',

                 'valueDsp')

    templateVrt = docgen.parseTemplate('''
        <div xmlns:py="http://genshi.edgewall.org/"
             py:if="res.og.hasRel(prop)"
             class="prop">
          <h2>${self.relName(prop)}</h2>

          ${valueDsp.displayVrt(valueSubgraph=res.og.valueSubgraph(prop))}
        </div>
        ''')

    def relName(self, uri):
        name = self.context.ogRelNames.get(uri)
        if name is not None:
            return name
        else:
            return self.context.model.shortenUri(uri)


class IcPropertyDisplay(docgen.Template):
    __slots__ = ()

    arguments = ('model',
                 'res',
                 'prop',
                 'icRelNames',

                 'valueDsp')

    templateVrt = docgen.parseTemplate('''
        <div xmlns:py="http://genshi.edgewall.org/"
             py:if="res.ic.hasRel(prop)"
             class="prop">
          <h2>${self.relName(prop)}</h2>

          ${valueDsp.displayVrt(valueSubgraph=res.ic.valueSubgraph(prop))}
        </div>
        ''')

    def relName(self, uri):
        name = self.context.icRelNames.get(uri)
        if name is not None:
            return name
        else:
            return self.context.model.shortenUri(uri)


class StdResTypeDisplay(docgen.Template):
    __slots__ = ()

    arguments = ('model',
                 'res',
                 'typeNames',)

    templateHrz = docgen.parseTemplate('''
        <span class="typeName">${self.typeName(res)}</span>
        ''')

    def typeName(self, res):
        tp = res.og.value(commonns.rdf.type)
        if tp is not None:
            name = self.context.typeNames.get(tp.uri)
            if name is not None:
                return name
            else:
                return self.context.model.shortenUri(tp.uri)
        else:
            return 'Resource'


class StdResNameDisplay(docgen.Template):
    __slots__ = ()

    arguments = ('model',
                 'res',
                 'nameProps',

                 'textValueDsp',)

    templateHrz = docgen.parseTemplate('''
        <span class="resName">${textValueDsp.displayHrz(valueSubgraph=
                                  self.getName(res))}</span>
        ''')

    def getName(self, res):
        for prop in self.context.nameProps:
            if res.og.hasRel(prop):
                return res.og.valueSubgraph(prop)

        return [(self.context.model.shortenUri(res.uri), None)]


class StdRdfResList(docgen.Template):
    __slots__ = ()

    arguments = ('model',
                 'valueSubgraph',
                 'typeSortOrder',

                 'resTypeDsp',
                 'resNameDsp',
                 'resLink',

                 'filterRes',
                 'resSortKey',)

    templateVrt = docgen.loadTemplate('reslist.genshi')

    def sortValueSubgraph(self, valueSubgraph):
        valueSubgraph = [(value, subgraph)
                         for value, subgraph in valueSubgraph
                         if self.context.filterRes(value)]
        valueSubgraph.sort(key=lambda (value, subgraph):
                                 self.context.resSortKey(value))
        return valueSubgraph

    def refClass(self, res, graph):
        return 'resRef'


class StdTextValueDisplay(docgen.Template):
    __slots__ = ()

    arguments = ('model',
                 'valueSubgraph',)

    templateHrz = docgen.parseTemplate('''
        <span xmlns:py="http://genshi.edgewall.org/"
              class="propValue">${self.formatValue(valueSubgraph)}</span>
        ''')

    def formatValue(self, valueSubgraph):
        # Pick the first value.
        return iter(valueSubgraph).next()[0]


class StdHtmlValueDisplay(docgen.Template):
    __slots__ = ()

    arguments = ('model',
                 'valueSubgraph',)

    templateVrt = docgen.parseTemplate('''
        <div xmlns:py="http://genshi.edgewall.org/"
             class="propValue">${self.formatValue(valueSubgraph)}</div>
        ''')

    arguments = ('model',
                 'valueSubgraph',
                 
                 'htmlFilter',)

    def formatValue(self, valueSubgraph):
        return self.prepareHtml(iter(valueSubgraph).next()[0])
    
    def prepareHtml(self, htmlText):
        try:
            # The value can be an XML 'forest'. Put it in an enclosing
            # element before parsing.
            stream = genshi.XML('<div>%s</div>' % htmlText)
        except:
            # We couldn't parse it. Return it in raw form.
            return htmlText

        return stream.filter(self.context.htmlFilter)

