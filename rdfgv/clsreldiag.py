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

    def formatProps(self, props, node):
        return ' '.join(['"%s%d"="%s"' % (key, node, value)
                         for (key, value) in props.items()])
                                    
    def addClass(self, rdfCls, labelProp, **props):
        params = {
            'rdfCls': rdfCls,
            'labelProp': labelProp,
            'props': self.formatProps(props, 1)
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
        select ?node1 "edge_label"="$label" "edge_color"="$color" ?node2
        where {
          $typeCond1
          $typeCond2
          graph relrdf:comp$comp {?node1 <$rdfRel> ?node2}
        }
        """)

    def getRelQuery(self, rdfRel, label, color, comp,
                    type1=None, type2=None):
        params = {
            'rdfRel': rdfRel,
            'label': label,
            'color': color,
            'comp': comp
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

    def addRelation(self, rdfRel, label, type1=None, type2=None):
        if self.old:
            print self.getRelQuery(rdfRel, label,
                                   'red', 'A',
                                   type1, type2)
            results = self.model.query('SPARQL',
                                       self.getRelQuery(rdfRel, label,
                                                        'red', 'A',
                                                        type1, type2))
            print len(results)
            self.addResults(results)

        print self.getRelQuery(rdfRel, label,
                               'black', 'AB',
                               type1, type2)
        results = self.model.query('SPARQL',
                                   self.getRelQuery(rdfRel, label,
                                                    'black', 'AB',
                                                    type1, type2))
        print len(results)
        self.addResults(results)

        if self.new:
            print self.getRelQuery(rdfRel, label,
                                   'green', 'B',
                                   type1, type2)
            results = self.model.query('SPARQL',
                                       self.getRelQuery(rdfRel, label,
                                                        'green', 'B',
                                                        type1, type2))
            print len(results)
            self.addResults(results)

