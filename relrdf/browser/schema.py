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


from relrdf.commonns import rdfs


class RdfSchemaError(Exception):
    pass


class RdfObject(object):
    __slots__ = ('uri',)

    def __init__(self, uri):
        self.uri = uri

    def __str__(self):
        return self.uri

    def getUri(self):
        return self.uri


class RdfClass(RdfObject):
    __slots__ = ('ancestors',
                 'descendants',
                 
                 'outgoingProps',
                 'incomingProps')

    def __init__(self, uri):
        super(RdfClass, self).__init__(uri)
        self.ancestors = set()
        self.descendants = set()
        self.outgoingProps = set()
        self.incomingProps = set()

    def addDescendant(self, descendant):
        self.descendants.add(descendant)
        descendant.ancestors.add(self)

    def printWithDescendants(self, indent=0):
        print "%s%s" % (' ' * indent, self)
        for d in self.descendants:
            d.printWithDescendants(indent + 2)

    def getAllOutgoingProps(self, exclude=None):
        """Return a set of all outgoing properties, including those of
        its parent classes."""
        result = set()
        self._getAllOutgoingProps(result, set())
        return result

    def _getAllOutgoingProps(self, result, visitedAncestors):
        result.update(self.outgoingProps)
        visitedAncestors.add(self)

        for ancestor in self.ancestors:
            # In case the class hierarchy has loops, we keep track of
            # already visited ancestors.
            if ancestor in visitedAncestors:
                continue
            ancestor._getAllOutgoingProps(result, visitedAncestors)

    def getAllIncomingProps(self, exclude=None):
        """Return a set of all Incoming properties, including those of
        its parent classes."""
        result = set()
        self._getAllIncomingProps(result, set())
        return result

    def _getAllIncomingProps(self, result, visitedAncestors):
        result.update(self.incomingProps)
        visitedAncestors.add(self)

        for ancestor in self.ancestors:
            # In case the class hierarchy has loops, we keep track of
            # already visited ancestors.
            if ancestor in visitedAncestors:
                continue
            ancestor._getAllIncomingProps(result, visitedAncestors)


class RdfProperty(RdfObject):
    __slots__ = ('domain',
                 'range')

    def __init__(self, uri):
        super(RdfProperty, self).__init__(uri)
        self.domain = set()
        self.range = set()

    def addToDomain(self, cls):
        self.domain.add(cls)
        cls.outgoingProps.add(self)

    def addToRange(self, cls):
        self.range.add(cls)
        if isinstance(cls, RdfClass):
            cls.incomingProps.add(self)


class RdfSchema(object):
    __slots__ = ('classes',
                 'properties')

    def __init__(self, model):
        # Build a table containing all defined classes:

        self.classes = {}

        # Some standard classes.
        self.classes[rdfs.Resource] = RdfClass(rdfs.Resource)
        self.classes[rdfs.Literal] = RdfClass(rdfs.Literal)

        for uri, in model.query('SPARQL',
                                """select ?class
                                where {?class rdf:type rdfs:Class}"""):
           self.classes[uri] = RdfClass(uri)

        for uri, nodeSub in \
                model.query('SPARQL',
                            """select ?class ?subclass
                            where {?subclass rdfs:subClassOf ?class}"""):
            try:
                cls = self.classes[uri]
                clsSub = self.classes[nodeSub]
            except KeyError:
                #print "Ignoring: %s is subclass of %s" \
                #      % (unicode(nodeSub).encode('utf-8'),
                #         unicode(uri).encode('utf-8'))
                continue

            cls.addDescendant(clsSub)


        # Build a table containing all defined properties.
        self.properties = {}

        for uri, in model.query('SPARQL',
                                 """select ?prop
                                 where {?prop rdf:type rdf:Property}"""):
           self.properties[uri] = RdfProperty(uri)

        for nodeProp, nodeCls in \
                model.query('SPARQL',
                            """select ?prop ?class
                            where {?prop rdfs:domain ?class}"""):
            try:
                prop = self.properties[nodeProp]

                cls = self.classes[nodeCls]
            except KeyError:
                #print "Ignoring: %s is in domain from %s" % \
                #      (unicode(nodeCls).encode('utf-8'),
                #       unicode(nodeProp).encode('utf-8'))
                continue

            prop.addToDomain(cls)

        for nodeProp, nodeCls in \
                model.query('SPARQL',
                            """select ?prop ?class
                            where {?prop rdfs:range ?class}"""):
            try:
                prop = self.properties[nodeProp]

                cls = self.classes[nodeCls]
            except KeyError:
                #print "Ignoring: %s is in range from %s" % \
                #      (unicode(nodeCls).encode('utf-8'),
                #       unicode(nodeProp).encode('utf-8'))
                continue

            prop.addToRange(cls)


