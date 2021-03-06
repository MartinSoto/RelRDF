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

import string

import rdfgv

import resulttransf


class ComparisonMaker(rdfgv.RdfGraphvizMaker):

    __slots__ = ('model',

                 'old',
                 'new')

    def __init__(self, graph, model, compType='full'):
        super(ComparisonMaker, self).__init__(graph)

        self.model = model

        if compType == 'old':
            self.old = True
            self.new = False
        elif compType == 'new':
            self.old = False
            self.new = True
        elif compType == 'full':
            self.old = True
            self.new = True
        else:
            assert False, compType

    classQuery = string.Template("""
        select ?node1 ?label1 "color1"="$color" $props
        where {
          graph relrdf:comp$comp {?node1 rdf:type <$rdfCls>}
          {?node1 <$labelProp> ?label1}
        }
        """)

    modifLabelQuery = string.Template("""
        select ?node1 ?oldName ?newName "fontcolor1"="red"
        where {
          graph relrdf:compAB {?node1 rdf:type <$rdfCls>}
          graph relrdf:compA {?node1 <$labelProp> ?oldName}
          graph relrdf:compB {?node1 <$labelProp> ?newName}
        }
        """)

    def formatNodeProps(self, props, node):
        return ' '.join(['"%s%d"="%s"' % (key, node, value)
                         for (key, value) in props.items()])
                                    
    def addClass(self, rdfCls, labelProp, **props):
        params = {
            'rdfCls': rdfCls,
            'labelProp': labelProp,
            'props': self.formatNodeProps(props, 1)
            }

        if self.old:
            params['color'] = 'red'
            params['comp'] = 'A'
            print self.classQuery.substitute(params)
            results = self.model.query('SPARQL',
                                       self.classQuery.substitute(params))
            print len(results)
            self.addResults(results)

        params['color'] = 'black'
        params['comp'] = 'AB'
        print self.classQuery.substitute(params)
        results = self.model.query('SPARQL',
                                   self.classQuery.substitute(params))
        print len(results)
        self.addResults(results)

        if self.new:
            params['color'] = 'green'
            params['comp'] = 'B'
            print self.classQuery.substitute(params)
            results = self.model.query('SPARQL',
                                       self.classQuery.substitute(params))
            print len(results)
            self.addResults(results)

        print self.modifLabelQuery.substitute(params)
        results = self.model.query('SPARQL',
                                   self.modifLabelQuery.substitute(params))
        print len(results)
        results = resulttransf.LabelFromOldNewName(results)
        self.addResults(results)

    relQuery = string.Template("""
        select ?node1 "edge_color"="$color" $props ?node2
        where {
          $typeCond1
          $typeCond2
          graph relrdf:comp$comp {?node1 <$rdfRel> ?node2}
        }
        """)

    def formatEdgeProps(self, props):
        return ' '.join(['"edge_%s"="%s"' % (key, value)
                         for (key, value) in props.items()])
                                    
    def getRelQuery(self, rdfRel, props, color, comp,
                    type1=None, type2=None):
        params = {
            'rdfRel': rdfRel,
            'color': color,
            'comp': comp,
            'props': self.formatEdgeProps(props)
            }

        if type1 is not None:
            params['typeCond1'] = "?node1 rdf:type <%s>" % type1
        else:
            params['typeCond1'] = ""

        if type2 is not None:
            params['typeCond2'] = "?node2 rdf:type <%s>" % type2
        else:
            params['typeCond2'] = ""

        return self.relQuery.substitute(params)

    def addRelation(self, rdfRel, type1=None, type2=None, **props):
        if self.old:
            print self.getRelQuery(rdfRel, props,
                                   'red', 'A',
                                   type1, type2)
            results = self.model.query('SPARQL',
                                       self.getRelQuery(rdfRel, props,
                                                        'red', 'A',
                                                        type1, type2))
            print len(results)
            self.addResults(results)

        print self.getRelQuery(rdfRel, props,
                               'black', 'AB',
                               type1, type2)
        results = self.model.query('SPARQL',
                                   self.getRelQuery(rdfRel, props,
                                                    'black', 'AB',
                                                    type1, type2))
        print len(results)
        self.addResults(results)

        if self.new:
            print self.getRelQuery(rdfRel, props,
                                   'green', 'B',
                                   type1, type2)
            results = self.model.query('SPARQL',
                                       self.getRelQuery(rdfRel, props,
                                                        'green', 'B',
                                                        type1, type2))
            print len(results)
            self.addResults(results)

