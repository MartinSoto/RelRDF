from commonns import xsd


class TypeNode(object):
    """A node in a type expression."""

    __slots__ = ('supertype')

    def __init__(self):
        self.supertype = None

    def isSubtype(self, typeExpr):
        """Return `True` iff `self` is a subtype of `typeExpr`."""
        curType = self
        while curType != None and curType != typeExpr:
            curType = curType.supertype
        return curType != None

    def intersectType(self, typeExpr):
        """Return a type expression corresponding to the most specific
        type between `self` and `typeExpr`, or `None` if they don't
        belong to the same line of the type hierarchy."""
        if self.isSubtype(typeExpr):
            return self
        elif typeExpr.isSubtype(self):
            return typeExpr
        else:
            return None        

    def generalizeType(self, typeExpr):
        """Return a type expression representing the most specific
        type that is a supertype of `self` and `typeExpr`, or
        `None` if no such type exists."""
        if self.isSubtype(typeExpr):
            return typeExpr
        elif typeExpr.isSubtype(self):
            return self
        else:
            return None

    def __str__(self):
        return self.__class__.__name__


class RdfNodeType(TypeNode):
    """A type node representing the generic type of RDF nodes. This is
    considered a supertype encompassing literals, blank nodes and
    resources."""

    __slots__ = ()

rdfNodeType = RdfNodeType()


class LiteralType(TypeNode):
    """A type node representing the type of an RDF literal. In can be
    open (a string) or it can be constrained to a type identified by a
    URI."""

    __slots__ = ('typeUri')

    def __init__(self, typeUri=None):
        super(LiteralType, self).__init__()

        self.supertype = rdfNodeType
        self.typeUri = typeUri

    def isSubtype(self, typeExpr):
        if isinstance(typeExpr, LiteralType):
            if typeExpr.typeUri == None:
                return True
            else:
                return self.typeUri == typeExpr.typeUri
        else:
            return super(LiteralType, self).isSubtype(typeExpr)

    def generalizeType(self, typeExpr):
        if isinstance(typeExpr, LiteralType):
            if self.typeUri == typeExpr.typeUri:
                return self
            else:
                return genericLiteralType
        else:
            return super(LiteralType, self).generalizeType(typeExpr)

    def __str__(self):
        if self.typeUri is not None:
            return '%s(<%s>)' % (self.__class__.__name__, self.typeUri)
        else:
            return self.__class__.__name__

genericLiteralType = LiteralType()
booleanLiteralType = LiteralType(xsd.boolean)


class BlankNodeType(TypeNode):
    """A type node representing the type of an RDF blank node."""

    __slots__ = ()

    def __init__(self, typeUri=None):
        super(BlankNodeType, self).__init__()

        self.supertype = rdfNodeType

blankNodeType = BlankNodeType()


class ResourceType(TypeNode):
    """A type node representing the type of a resource."""

    __slots__ = ()

    def __init__(self, typeUri=None):
        super(ResourceType, self).__init__()

        self.supertype = rdfNodeType

resourceType = ResourceType()


class RelationType(TypeNode):
    """A node type representing the type of a relation. A relation
    type is essentially a dictionary relating column names and basic
    types. For convenience reasons, column names are arbitrary objects
    that are only required to have a __hash__ method. Database
    mappings can use names to directly refer to entities relevant to
    the mapping, like SQL columns."""

    __slots__ = ('dict')

    def __init__(self):
        super(RelationType, self).__init__()

        self.dict = {}

    def addColumn(self, name, typeExpr):
        self.dict[name] = typeExpr

    def getColumnNames(self):
        """Return a set containing the column names."""
        return set(self.dict.keys())

    def getColumnType(self, columnName):
        try:
            return self.dict[columnName]
        except KeyError:
            return None

    def hasColumn(self, columnName):
        """Return `True` iff `self` has a column named `columnName`."""
        return columnName in self.dict

    def isSubtype(self, typeExpr):
        if not isinstance(typeExpr, RelationType) or \
           self.getColumnNames() != typeExpr.getColumnNames():
            return False

        for colName, colType in self.dict.items():
            if not colType.isSubtype(typeExpr.getColumnType(colName)):
                return False

        return True

    def generalizeType(self, typeExpr):
        if not isinstance(typeExpr, RelationType) or \
           self.getColumnNames() != typeExpr.getColumnNames():
            return None

        common = RelationType()
        for colName, colType in self.dict.items():
            colCommon = colType.generalizeType(typeExpr.getColumnType(colName))
            if colCommon is None:
                return None

            common.addColumn(colName, colCommon)

        return common

    def __str__(self):
        cols = []
        for item in self.dict.items():
            cols.append('%s: %s' % item)
        return '%s(%s)' % (self.__class__.__name__, ', '.join(cols))
