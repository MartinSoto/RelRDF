#!/usr/bin/python

import sets

from commonns import rdfs
import prefixes


class RdfSchemaError(Exception):
    pass


LITERAL = rdfs.Literal


class RdfObject(object):
    __slots__ = ('node',)

    def __init__(self, node):
        self.node = node

    def __str__(self):
        return prefixes.shortenUri(self.node)


class RdfClass(RdfObject):
    __slots__ = ('ancestors',
                 'descendants',
                 
                 'properties')

    def __init__(self, node):
        super(RdfClass, self).__init__(node)
        self.ancestors = sets.Set()
        self.descendants = sets.Set()
        self.properties = sets.Set()

    def addDescendant(self, descendant):
        self.descendants.add(descendant)
        descendant.ancestors.add(self)

    def addProperty(self, property, range):
        self.properties[property] = range

    def printWithDescendants(self, indent=0):
        print "%s%s" % (' ' * indent, self)
        for d in self.descendants:
            d.printWithDescendants(indent + 2)


class RdfProperty(RdfObject):
    __slots__ = ('domain',
                 'range')

    def __init__(self, node):
        super(RdfProperty, self).__init__(node)
        self.domain = sets.Set()
        self.range = sets.Set()

    def addToDomain(self, cls):
        self.domain.add(cls)
        cls.properties.add(self)

    def addToRange(self, cls):
        self.range.add(cls)


class RdfSchema(object):
    __slots__ = ('classes',
                 'properties')

    def __init__(self, model):
        # Build a table containing all defined classes.
        self.classes = {}
        for node, in model.query('SerQL',
                                 """select class
                                 from {class} rdf:type {rdfs:Class}"""):
           self.classes[node] = RdfClass(node)

        for node, nodeSub in \
                model.query('SerQL',
                            """select class, subclass
                            from {subclass} rdfs:subClassOf {class}"""):
            try:
                cls = self.classes[node]
                clsSub = self.classes[nodeSub]
            except KeyError:
                print "Ignoring: %s is subclass of %s" \
                      % (nodeSub, node)
                continue

            cls.addDescendant(clsSub)


        # Build a table containing all defined properties.
        self.properties = {}

        for node, in model.query('SerQL',
                                 """select prop
                                 from {prop} rdf:type {rdf:Property}"""):
           self.properties[node] = RdfProperty(node)

        for nodeProp, nodeCls in \
                model.query('SerQL',
                            """select prop, class
                            from {prop} rdfs:domain {class}"""):
            try:
                prop = self.properties[nodeProp]

                if nodeCls == LITERAL:
                    cls = LITERAL
                else:
                    cls = self.classes[nodeCls]
            except KeyError:
                print "Ignoring: %s is in domain from %s" % (nodeCls,
                                                             nodeProp)
                continue

            prop.addToDomain(cls)

        for nodeProp, nodeCls in \
                model.query('SerQL',
                            """select prop, class
                            from {prop} rdfs:range {class}"""):
            try:
                prop = self.properties[nodeProp]

                if nodeCls == LITERAL:
                    cls = LITERAL
                else:
                    cls = self.classes[nodeCls]
            except KeyError:
                print "Ignoring: %s is in range from %s" % (nodeCls,
                                                            nodeProp)
                continue

            prop.addToRange(cls)


if __name__ == "__main__":
    import sys
    
    file = sys.argv[1]

    s = RdfSchema(file)

    for cls in s.classes.values():
        print cls
        for prp in cls.properties:
            print "  " + str(prp)
