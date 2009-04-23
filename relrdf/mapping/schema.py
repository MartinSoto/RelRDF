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
from relrdf import error
from relrdf.expression import nodes

import macro
import mapper


class SchemaObject(object):
    """Base class for objects in a schema."""

    __slots__ = ('name',
                 'extents',)

    def __init__(self, name):
        # The `name` parameter is a `nodes.Literal` node.
        self.name = unicode(name.literal)

        # Initially, we use extents of the element's name.
        self.extents = name.getExtents()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

    def getExtents(self):
        """Return a `nodes.NodeExtents` object with the extents of
        this object."""
        return self.extents

    def setExtentsStartFromToken(self, token, parser=None):
        """Set the start fields of `self`'s extents to the start of
        the provided token, and use the file name from the provided
        parser."""
        self.extents.setStartFromToken(token, parser)

    def setExtentsEndFromToken(self, token, extraLength=0):
        """Set the end fields of `self`'s extents to the end of the
        provided token. See `nodes.NodeExtents.setEndFromToken` for
        the meaning of `extraLength`."""
        self.extents.setEndFromToken(token, extraLength=extraLength)

    def setExtentsFromToken(self, token, parser=None, extraLength=0):
        """Set `self`'s extents to the extents of the provided token,
        and use the file name from the provided parser. See
        `nodes.NodeExtents.setEndFromToken` for the meaning of
        `extraLength`."""
        self.extents.setFromToken(token, parser,
                                  extraLength=extraLength)


INDEX_OPT_UNIQUE = 1
INDEX_OPT_PRIMARY = 2

class Index(SchemaObject):
    """A SQL database index."""

    __slots__ = ('table',
                 'columns',
                 'options',)

    def __init__(self, name, table):
        super(Index, self).__init__(name)

        self.table = table

        self.columns = set()
        self.options = set()

    def addColumn(self, colName):
        # `colName` is a `nodes.Literal`.
        column = self.table.getColumn(colName)

        if column in self.columns:
            raise error.SyntaxError(msg=_("Column '%s' specified twice for "
                                          "index '%s'") %
                                    (unicode(colName.literal),
                                     self.name),
                                    extents=colName.getExtents())

        self.columns.add(column)


COL_OPT_NOT_NULL = 1
COL_OPT_AUTO_INCR = 2

class Column(SchemaObject):
    """A SQL table column."""

    __slots__ = ('typeUri',
                 'options',)

    def __init__(self, name, typeUri=None, options=set()):
        super(Column, self).__init__(name)

        self.typeUri = typeUri
        self.options = options


class Table(SchemaObject):
    """A SQL table."""

    __slots__ = ('options',
                 'columns',
                 'indexes',)

    def __init__(self, name, options=set()):
        super(Table, self).__init__(name)

        self.options = options

        self.columns = {}
        self.indexes = set()

    def addColumn(self, column):
        if column.name in self.columns:
            raise error.SyntaxError(msg=_("Redefinition of column '%s'") %
                                    column.name,
                                    extents=column.getExtents())

        self.columns[column.name] = column

    def getColumn(self, colName):
        # `colName` is a `nodes.Literal`.
        try:
            return self.columns[unicode(colName.literal)]
        except KeyError:
            raise error.SyntaxError(msg=_("Table '%s' has no column '%s'") %
                                    (self.name,
                                     unicode(colName.literal)),
                                    extents=colName.getExtents())

    def addIndex(self, index):
        if index.name in self.indexes:
            raise error.SyntaxError(msg=_("Redefinition of index '%s.%s'") %
                                    (self.name, column.name),
                                    extents=index.getExtents())

        self.indexes[index.name] = index


class MacroDef(SchemaObject):
    """An object representing a schema macro definition."""

    __slots__ = ('closure',)

    def __init__(self, name, closure):
        super(MacroDef, self).__init__(name)

        self.closure = closure


class MappingDef(SchemaObject):
    """An object representing a schema mapping definition."""

    __slots__ = ('params',
                 'matchClauses',
                 'defCls',)

    def __init__(self, name, params):
        super(MappingDef, self).__init__(name)

        self.params = params

        self.matchClauses = []
        self.defCls = None

    def addMatch(self, pattern, expr, cond=None):
        # Calculate the actual parameters and corresponding argument
        # positions.
        argPos = []
        params = []
        for i, elem in enumerate(pattern):
            if elem is not None:
                argPos.append(i)
                params.append(elem)

        # The matching closures are dependent both on the pattern and
        # on the mapping parameters.
        exprCls = macro.MacroClosure(params, None, expr)
        exprCls = macro.MacroClosure(self.params, None, exprCls)
        if cond is not None:
            condCls = macro.MacroClosure(params, None, cond)
            condCls = macro.MacroClosure(self.params, None, condCls)
        else:
            condCls = None

        self.matchClauses.append((argPos, exprCls, condCls))

    def setDefault(self, expr):
        self.defCls = macro.MacroClosure(self.params, None, expr)

    def getMapper(self, **keywords):
        # Calculate the arguments only once.
        args = self.defCls.argsFromKeywords(keywords, objName=self.name)

        mp = mapper.MacroMapper()
        for argPos, exprCls, condCls in self.matchClauses:
            exprCls = exprCls.expandFromValues(*args)
            if condCls is not None:
                condCls = condCls.expandFromValues(*args)
            mp.addMatch(argPos, exprCls, condCls)

        mp.setDefault(self.defCls.expandFromValues(*args))

        return mp


class Schema(object):
    """A complete schema definition."""

    __slots__ = ('defs')

    def __init__(self):
        self.defs = {}

    def addDef(self, defObj):
        if defObj.name in self.defs:
            raise error.SyntaxError(msg=_("Redefinition of '%s'") %
                                          defObj.name,
                                    extents=defObj.getExtents())

        self.defs[defObj.name] = defObj

    def getObj(self, name):
        """Return the schema object named by `name`.

        `name` is a `nodes.Literal`. If no object of the given name
        is defined in the schema, an exception is thrown."""
        try:
            return self.defs[unicode(name.literal)]
        except KeyError:
            raise error.SyntaxError(msg=_("Undefined object '%s'") %
                                          unicode(name.literal),
                                    extents=name.getExtents())

    def getTable(self, name):
        """Return the schema table object named by `name`.

        `name` is a `nodes.Literal`. If no table of the given
        name is defined in the schema, an exception is thrown."""
        table = self.getObj(name)
        if not isinstance(table, Table):
            raise error.SyntaxError(msg=_("'%s' is not a table") %
                                          unicode(name.literal),
                                    extents=name.getExtents())

        return table

    def getMacro(self, name):
        """Return the body of the schema macro named by `name`.

        `name` is string. The return value is the closure
        corresponding to the macro definition or None if no macro of
        this name is defined in the schema."""
        try:
            macroDef = self.defs[name]
        except KeyError:
            return None

        if not isinstance(macroDef, MacroDef):
            return None

        return macroDef.closure

    def getMapper(self, name, **keywords):
        """Return the mapper object defined by mapping `name`
        and the keyword parameters.

        `name` is a string."""
        try:
            mappingDef = self.defs[name]
        except KeyError:
            mappingDef = None

        if mappingDef is None or not isinstance(mappingDef, MappingDef):
            raise error.InstantiationError(_("Undefined mapping '%s'") %
                                           name)

        return mappingDef.getMapper(**keywords)

