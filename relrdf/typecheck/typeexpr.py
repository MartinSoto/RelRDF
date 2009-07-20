# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2009 Fraunhofer-Institut fuer Experimentelles
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


from relrdf.localization import _

from relrdf.commonns import xsd
from relrdf.error import TypeCheckError


def error(expr, msg):
    raise TypeCheckError(extents=expr.getExtents(), msg=msg)


class TypeNode(object):
    """A node in a type expression."""

    __slots__ = ('supertype',)

    def __init__(self):
        self.supertype = None

    def isSubtype(self, typeExpr):
        """Return `True` iff `self` is a subtype of `typeExpr`."""
        curType = self
        while curType is not None and curType != typeExpr:
            curType = curType.supertype
        return curType is not None

    def intersectType(self, typeExpr):
        """Return a type expression corresponding to the most specific
        type between `self` and `typeExpr`, or `nullType` if they
        don't belong to the same line of the type hierarchy."""
        if self.isSubtype(typeExpr):
            return self
        elif typeExpr.isSubtype(self):
            return typeExpr
        else:
            return nullType

    def generalizeType(self, typeExpr):
        """Return a type expression representing the most specific
        type that is a supertype of `self` and `typeExpr`, or
        `nullType` if no such type exists."""
        if self.isSubtype(typeExpr):
            return typeExpr
        elif typeExpr.isSubtype(self):
            return self
        else:
            return nullType

    def __str__(self):
        return self.__class__.__name__


def commonType(*exprs):
    """Return a type expression representing the most specific type
    that is a supertype of the types of all elements in `exprs`, or
    `nullType` if no such type exists."""
    if len(exprs) == 0 or exprs[0].staticType is None:
        return nullType

    genType = exprs[0].staticType
    for expr in exprs[1:]:

        if expr.staticType is None:
            return nullType

        genType = genType.generalizeType(expr.staticType)

    return genType


class NullType(TypeNode):
    """A type node representing the null type. This type is used when
    no other type can be determined for an expression, for example,
    when there are unbound variables in the expression."""

    __slots__ = ()

nullType = NullType()


class TypeType(TypeNode):
    """A type node representing the type of interal type identifiers"""

    __slots__ = ()

typeType = TypeType()

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

    __slots__ = ('typeUri',)

    def __init__(self, typeUri=None):
        super(LiteralType, self).__init__()

        self.supertype = rdfNodeType
        self.typeUri = typeUri

    def isSubtype(self, typeExpr):
        if isinstance(typeExpr, LiteralType):
            if typeExpr.typeUri is None:
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

    __slots__ = ('dict',)

    def __init__(self):
        super(RelationType, self).__init__()

        self.dict = {}

    def addColumn(self, name, typeExpr):
        assert typeExpr is not None
        self.dict[name] = typeExpr

    def getColumnNames(self):
        """Return a set containing the column names."""
        return set(self.dict.keys())

    def getColumnType(self, columnName):
        try:
            return self.dict[columnName]
        except KeyError:
            return nullType

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
            return nullType

        common = RelationType()
        for colName, colType in self.dict.items():
            colCommon = colType.generalizeType(typeExpr.getColumnType(colName))
            if colCommon == nullType:
                return nullType

            common.addColumn(colName, colCommon)

        return common

    def joinType(self, relTypeExpr):
        """Add the columns in `relTypeExpr` to `self`. If columns with
        the same name are present in both types, a single column will
        be created with the intersection type of both columns."""
        for columnName in relTypeExpr.getColumnNames():
            if self.hasColumn(columnName):
                columnType = self.getColumnType(columnName). \
                             intersectType(relTypeExpr. \
                                           getColumnType(columnName))
                if columnType == nullType:
                    error(expr, _("Incompatible types for variable '%s'")
                          % columnName)
            else:
                columnType = relTypeExpr.getColumnType(columnName)
            self.addColumn(columnName, columnType)

    def unionType(self, relTypeExpr):
        """Add the columns in `relTypeExpr` to `self`. If columns with
        the same name are present in both types, a single column will
        be created with the generalized type of both columns."""
        for columnName in relTypeExpr.getColumnNames():
            if self.hasColumn(columnName):
                columnType = self.getColumnType(columnName). \
                             generalizeType(relTypeExpr. \
                                           getColumnType(columnName))
                if columnType == nullType:
                    error(expr, _("Incompatible types for variable '%s'")
                          % columnName)
            else:
                columnType = relTypeExpr.getColumnType(columnName)
            self.addColumn(columnName, columnType)

    def __str__(self):
        cols = []
        for item in self.dict.items():
            cols.append('%s: %s' % item)
        return '%s(%s)' % (self.__class__.__name__, ', '.join(cols))


class StatementRelType(RelationType):
    """A node type representing a set of RDF statements. This is
    actually a relation type that contains columns corresponding to
    subject, predicate and object of the statements. It is possible
    for a single row of a statement relation type to contain more than
    one statement. In this case, the number of columns is always a
    multiple of three and the sequence of subject, predicate and
    object repeats itself for each statement.
    """

    __slots__ = ()
