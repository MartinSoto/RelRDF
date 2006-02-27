#!/usr/bin/python

import sets

import RDF

import prefixes
import query


class RdfSchemaError(Exception):
    pass


class Literal(object):
    __slots__ = ()

    URI = 'http://www.w3.org/2000/01/rdf-schema#Literal'

    def __str__(self):
        return self.URI

# Singleton object.
LITERAL = Literal()


class RdfObject(object):
    __slots__ = ('node')

    def __init__(self, node):
        self.node = node

    def __str__(self):
        return prefixes.shortenUri(str(self.node.uri))


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

    def __init__(self, fileNameOrModel):
        if isinstance(fileNameOrModel, str):
            model = query.Model(fileNameOrModel)
        else:
            model = fileNameOrModel

        # Build a table containing all defined classes.
        self.classes = {}
        for result in model.query("""SELECT ?class
                                  WHERE (?class, rdf:type, rdfs:Class)"""):
           node = result['class']
           self.classes[node] = RdfClass(node)

        for result in model.query("""SELECT ?class, ?subclass
                                  WHERE (?subclass, rdfs:subClassOf, ?class)"""):
            node = result['class']
            nodeSub = result['subclass']

            try:
                cls = self.classes[node]
                clsSub = self.classes[nodeSub]
            except KeyError:
                print "Ignoring: %s is subclass of %s" \
                      % (nodeSub.uri, node.uri)
                continue

            cls.addDescendant(clsSub)


        # Build a table containing all defined properties.
        self.properties = {}

        for result in model.query("""SELECT ?prop
                                  WHERE (?prop, rdf:type, rdf:Property)"""):
           node = result['prop']
           self.properties[node] = RdfProperty(node)

        for result in model.query("""SELECT ?prop, ?class
                                  WHERE (?prop, rdfs:domain, ?class)"""):
            nodeProp = result['prop']
            nodeCls = result['class']

            try:
                prop = self.properties[nodeProp]

                if str(nodeCls.uri) == str(LITERAL):
                    cls = LITERAL
                else:
                    cls = self.classes[nodeCls]
            except KeyError:
                print "Ignoring: %s is in domain from %s" % (nodeCls.uri,
                                                             nodeProp.uri)
                continue

            prop.addToDomain(cls)

        for result in model.query("""SELECT ?prop, ?class
                                  WHERE (?prop, rdfs:range, ?class)"""):
            nodeProp = result['prop']
            nodeCls = result['class']

            try:
                prop = self.properties[nodeProp]

                if str(nodeCls.uri) == str(LITERAL):
                    cls = LITERAL
                else:
                    cls = self.classes[nodeCls]
            except KeyError:
                print "Ignoring: %s is in range from %s" % (nodeCls.uri,
                                                             nodeProp.uri)
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
