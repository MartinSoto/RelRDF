from relrdf import error
from relrdf.expression import nodes

import valueref
import transform
import macro


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


class MacroValueMapping(valueref.ValueMapping):
    """A value mapping based on schema macro expressions."""

    __slots__ = ('intToExtCls',
                 'extToIntCls',)

    def __init__(self, intToExtCls, extToIntCls):
        self.intToExtCls = intToExtCls
        self.extToIntCls = extToIntCls

    def intToExt(self, internal):
        return self.intToExtCls.expand(internal)

    def extToInt(self, external):
        return self.extToIntCls.expand(external)


class ValueMappingDef(SchemaObject):
    """An object representing a schema value mapping definition."""

    __slots__ = ('valueMapping',)

    def __init__(self, name, params, intToExtDef, extToIntDef):
        super(ValueMappingDef, self).__init__(name)

        intToExtExpr = self._processDef(intToExtDef, 'intToExt', params)
        extToIntExpr = self._processDef(intToExtDef, 'intToExt', params)
        
        self.valueMapping = MacroValueMapping(intToExtExpr, extToIntExpr)

    def _processDef(self, macroDef, expectedName, params):
        # Check the name.
        if macroDef.name.lower() != expectedName.lower():
            raise error.SyntaxError(_("Definition for '%s' expected") %
                                    expectedName,
                                    extents=macroDef.getExtents())

        # Extract the actual closure and check the number of
        # parameters.
        closure = macroDef.closure
        if len(closure.params) != 1:
            raise error.SyntaxError(_("Definition must have exactly one "
                                      "parameter"),
                                    extents=macroDef.getExtents())

        # Wrap the closure in a second closure to handle the mapping
        # parameters.
        closure = macro.MacroClosure(params, None, closure)

        return closure


class MacroMapper(transform.PureRelationalTransformer):
    """A mapper based on macro expressions."""
    pass


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
