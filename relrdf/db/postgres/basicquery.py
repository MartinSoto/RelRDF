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


import string
import re

import relrdf

from relrdf.localization import _
from relrdf.error import InstantiationError, ModifyError
from relrdf import results, mapping, parsequery, commonns

from relrdf.typecheck import dynamic
from relrdf.expression import uri, literal, nodes, build, simplify
from relrdf.mapping import transform, valueref, sqlnodes, emit, sqltranslate

from relrdf.typecheck.typeexpr import LiteralType, BlankNodeType, \
     ResourceType, RdfNodeType, resourceType, rdfNodeType

from basicsinks import SingleGraphRdfSink

from relrdf.util import nsshortener

def resourceTypeExpr():
    return nodes.Uri(commonns.rdfs.Resource)

class GraphUriMapping(valueref.ValueMapping):
    """A value mapping converting graph IDs into graph URIs and back."""

    __slots__ = ()

    # Give this type of mapping priority in comparisons.
    weight = 80

    def _subqueryGraph(self, field, value, resultField):

        # Build a nested query on the "graphs" table
        (expr,) = transform.Incarnator.reincarnate(nodes.MapValue(
                nodes.Select(
                     sqlnodes.SqlRelation(1, 'graphs'),
                     nodes.Equal(
                          sqlnodes.SqlFieldRef(1, field),
                          nodes.Null()
                     )
                ),
                sqlnodes.SqlFieldRef(1, resultField)
            ))

        # Replace null by actual ID (done late so it won't reincarnate)
        assert isinstance(expr[0][1][1], nodes.Null)
        expr[0][1][1] = value

        return expr

    def intToExt(self, internal):
        return sqlnodes.SqlFunctionCall('rdf_term_resource',
                                        self._subqueryGraph('graph_id', internal, 'graph_uri'))

    def extToInt(self, external):
        return self._subqueryGraph('graph_uri',
                                   sqlnodes.SqlFunctionCall('text',
                                                            sqlnodes.SqlFunctionCall('rdf_term_to_string', external)),
                                   'graph_id')

def graphUriRef(incarnation, fieldId):
    return valueref.ValueRef(GraphUriMapping(),
                             sqlnodes.SqlFieldRef(incarnation, fieldId))

class TypeMapping(valueref.ValueMapping):
    """A value mapping that uses type IDs as listed in the
    types SQL table instead of the full type URIs used
    by RDF"""

    __slots__ = ('property')

    def __init__(self, property):
        self.property = property
        super(TypeMapping, self).__init__()

    def intToExt(self, internal):
        return sqlnodes.SqlFunctionCall('rdf_term_%s_by_id' % self.property, internal)

    def extToInt(self, external):
        return sqlnodes.SqlFunctionCall('rdf_term_%s_to_id' % self.property, external)

def typeValueRef(incarnation, fieldId):

    valueExpr = sqlnodes.SqlFieldRef(incarnation, fieldId);
    typeIdExpr = sqlnodes.SqlFunctionCall('rdf_term_get_data_type_id', valueExpr)

    return valueref.ValueRef(TypeMapping('type_uri'), typeIdExpr)

def valueRef(incarnation, fieldId):
    return sqlnodes.SqlTypedFieldRef(incarnation, fieldId)

class BasicMapper(transform.PureRelationalTransformer):
    """A base mapper for the Postgres basic schema. It handles the
    mapping of type expressions."""

    __slots__ = ()

    def mapTypeExpr(self, typeExpr):
        if isinstance(typeExpr, LiteralType):
            assert not typeExpr.typeUri is None
            return nodes.Uri(typeExpr.typeUri)
        elif isinstance(typeExpr, ResourceType):
            return resourceTypeExpr()
        else:
            assert False, "Cannot determine type"

    def getModifGraph(self):
        """Returns the URI of the graph that should receive modifications."""
        raise NotImplementedError

    def DynType(self, expr, subexpr):
        typeIdExpr = sqlnodes.SqlFunctionCall('rdf_term_get_data_type_id', subexpr)
        return valueref.ValueRef(TypeMapping('type_uri'), typeIdExpr)

    def Lang(self, expr, subexpr):
        typeIdExpr = sqlnodes.SqlFunctionCall('rdf_term_get_lang_type_id', subexpr)
        return valueref.ValueRef(TypeMapping('lang_tag'), typeIdExpr)

class BasicGraphMapper(BasicMapper):

    __slots__ = ('modelBase',
                 'baseGraph',
                 'baseGraphId',
                 'stmtReplDefault',
                 'stmtReplOther')

    def __init__(self, modelBase, baseGraph):
        super(BasicGraphMapper, self).__init__()

        self.modelBase = modelBase
        self.baseGraph = baseGraph

        # Cache for the statement pattern replacement expressions.
        self.stmtReplDefault = None
        self.stmtReplOther = None

    def _getDefaultGraph(self):
        return valueref.ValueRef(GraphUriMapping(),
                                 sqlnodes.SqlInt(self.baseGraphId));

    def replStatementPattern(self, expr):
        # Always either select the default graph or the rest.
        if isinstance(expr[0], nodes.DefaultGraph):
            graphSelector = nodes.Equal(sqlnodes.SqlFieldRef(1, 'graph_id'),
                                        sqlnodes.SqlInt(self.baseGraphId))
        else:
            graphSelector = nodes.Different(sqlnodes.SqlFieldRef(1, 'graph_id'),
                                            sqlnodes.SqlInt(self.baseGraphId))

        rel = nodes.Select(
             nodes.Product(
              sqlnodes.SqlRelation(1, 'graph_statement'),
              sqlnodes.SqlRelation(2, 'statements')),
             nodes.And(
              nodes.Equal(
               sqlnodes.SqlFieldRef(1, 'stmt_id'),
               sqlnodes.SqlFieldRef(2, 'id')),
              graphSelector))

        replExpr = \
          nodes.MapResult(['context', 'subject', 'predicate', 'object'],
                          rel,
                          graphUriRef(1, 'graph_id'),
                          valueRef(2, 'subject'),
                          valueRef(2, 'predicate'),
                          valueRef(2, 'object'))

        return (replExpr,
                ('context', 'subject', 'predicate', 'object'))

    # TODO: This should belong to a more generic superclass.
    def Project(self, expr, *subexprs):
        # Create an incarnation for the project expression.
        incarnation = transform.Incarnator.makeIncarnation()

        # Bind the column names to appropriate expressions. Also,
        # generate valid SQL name for the columns.
        for i, name in enumerate(expr.columnNames):
            sqlName = 'col_%d' % (i + 1)
            self.varBindings[name] = valueRef(incarnation, sqlName)
            expr.columnNames[i] = sqlName

        return sqlnodes.SqlAs(incarnation, expr)

    # TODO: This should belong to a more generic superclass.
    def preUnion(self, expr):
        for subexpr in expr:
            # This must be a projection expression.
            assert isinstance(subexpr, nodes.Project)

            # Process all of its subexpressions first.
            for i, ssexpr in enumerate(subexpr):
                subexpr[i] = self.process(ssexpr)

            # Replace the column names by valid SQL names. These names
            # are identical to those used by the union, so the Union
            # method will bind them properly.
            subexpr.columnNames = ['col_%d' % (i + 1)
                                   for i in xrange(len(subexpr.columnNames))]

        return expr

    # TODO: This should belong to a more generic superclass.
    def Union(self, expr, *subexprs):
        # Create an incarnation for the whole union.
        incarnation = transform.Incarnator.makeIncarnation()

        # Bind the column names to appropriate expressions. Also,
        # generate valid SQL name for the columns.
        for i, name in enumerate(expr.columnNames):
            sqlName = 'col_%d' % (i + 1)
            self.varBindings[name] = valueRef(incarnation, sqlName)
            expr.columnNames[i] = sqlName

        return sqlnodes.SqlAs(incarnation, expr)

    def process(self, expr):
        # Lookup the base graph for every transformation.
        self.baseGraphId = self.modelBase.lookupGraphId(self.baseGraph)

        return super(BasicGraphMapper, self).process(expr)


class GraphMapper(BasicGraphMapper, transform.StandardReifTransformer):

    __slots__ = ()

    name = "Single Graph"
    parameterInfo = ({"name":"graphId", "label":"Graph ID", "tip":"Enter the ID of the graph to be used", "assert":"graphId != ''", "asserterror":"Graph ID must not be empty"},)

    def __init__(self, modelBase, baseGraph, **args):
        super(GraphMapper, self).__init__(modelBase, baseGraph)

    def getModifGraph(self):
        return self.baseGraph

class BaseResults(object):
    __slots__ = ('connection',
                 'cursor',
                 'length',
                 'types',)

    def __init__(self, connection, sqlText):
        self.connection = connection
        self.cursor = connection.cursor()

        # Send the query to the database (iterating on this object
        # will produce the actual results.)
        if isinstance(sqlText, unicode):
            sqlText = sqlText.encode('utf-8')
        self.cursor.execute(sqlText)

        self.length = self.cursor.rowcount

        self.types = {}

    def resultType(self):
        return NotImplemented

    def __len__(self):
        return self.length

    def _typeLookup(self, typeId):

        # Try cache lookup first
        try:
            return self.types[typeId]
        except KeyError:
            pass

        # Query database for information about type ID
        cursor = self.connection.cursor()
        cursor.execute("SELECT type_uri, lang_tag FROM types WHERE id = %d" % typeId);
        result = cursor.fetchone()

        # Not in database? (Should not happen)
        assert not result is None, "Database result uses unknown type ID %d!" % typeId

        # Save back, continue
        self.types[typeId] = result
        return result

    def _convertResult(self, rawValue, typeId, blankMap):
        if isinstance(rawValue, str):
            try:
                rawValue = rawValue.decode('utf8')
            except UnicodeDecodeError:
                rawValue = "<<Character encoding error>>"

        if rawValue is None:
            value = None

        # Resource
        elif typeId == 0:
            value = uri.Uri(rawValue)

            # Needs reinstantiation?
            if value.isBlank() and value.endswith('#reinst'):
                try:
                    value = blankMap[rawValue]
                except KeyError:
                    value = blankMap[rawValue] = uri.newBlank()

        # Plain literal
        elif typeId == 1:
            value = literal.Literal(rawValue)

        # Literal
        else:

            # Get type URI and language tag
            (typeUri, langTag) = self._typeLookup(typeId)

            # Expect everything that's not a resource to be some
            # sort of literal
            value = literal.Literal(rawValue, typeUri, langTag)

        return value

    def _splitPair(self, pair):

        # Split the string representation of a value/type-id pair
        # as it's coming from the database into both components
        # (Note the first part is enclosed in quotes and the second
        #  one is a hexadecimal number)

        if pair is None:
            return (None, None)
        else:
            (val, _, typeId) = pair.rpartition('^^')
            return (val[1:-1], int(typeId, 16))

    def close(self):
        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None

    def __del__(self):
        if self.cursor is not None:
            try:
                self.cursor.close()
            except:
                # Ignore exceptions if the cursor cannot be closed.
                pass


class ColumnResults(BaseResults):
    __slots__ = ('columnNames',)

    def __init__(self, connection, columnNames, sqlText):
        super(ColumnResults, self).__init__(connection, sqlText)
        self.columnNames = columnNames

    def resultType(self):
        return results.RESULTS_COLUMNS

    def iterAll(self):
        row = self.cursor.fetchone()
        while row is not None:
            result = []
            blankMap = {}
            for pair in row:
                (val, type) = self._splitPair(pair)
                result.append(self._convertResult(val, type, blankMap))
            yield tuple(result)

            row = self.cursor.fetchone()

        self.close()

    __iter__ = iterAll


class StmtResults(BaseResults):
    __slots__ = ('stmtsPerRow',)

    def __init__(self, connection, stmtsPerRow, sqlText):
        super(StmtResults, self).__init__(connection, sqlText)
        self.stmtsPerRow = stmtsPerRow
        self.length *= stmtsPerRow

    def resultType(self):
        return results.RESULTS_STMTS

    def iterAll(self):
        row = self.cursor.fetchone()
        while row is not None:

            # The blank node reinstationation map is kept across statements, as
            # statements in the same row might refer to the same blank nodes.
            blankMap = {}

            for i in range(self.stmtsPerRow):
                result = []
                for pair in row[i*3 : i*3+3]:
                    (val, type) = self._splitPair(pair)
                    result.append(self._convertResult(val, type, blankMap))
                yield tuple(result)

            row = self.cursor.fetchone()

        self.close()

    __iter__ = iterAll


class ExistsResults(BaseResults):
    __slots__ = ('_value',)

    def __init__(self, connection, sqlText):
        super(ExistsResults, self).__init__(connection, sqlText)
        self._value = None

    def resultType(self):
        return results.RESULTS_EXISTS

    def getValue(self):
        if self._value is None:
            # Retrieve the value.
            assert self.length == 1
            row = self.cursor.fetchone()
            assert len(row) == 1
            self._value = row[0]

        return self._value

    value = property(getValue)


class BasicModel(object):
    __slots__ = ('modelBase',
                 'mappingTransf',
                 'modelArgs',
                 '_connection',
                 '_changeCursor',)

    def __init__(self, modelBase, connection, mappingTransf, **modelArgs):
        self.modelBase = modelBase
        self.mappingTransf = mappingTransf
        self.modelArgs = modelArgs
        self._connection = connection

        # The change cursor is initialized when actual changes are in
        # progress.
        self._changeCursor = None

    def _exprToSql(self, expr):
        # Transform occurrences of StatementResult
        expr = transform.StatementResultTransformer().process(expr)

        # Insert known type information
        expr = dynamic.dynTypeTranslate(expr)

        # Apply the selected mapping.
        expr = self.mappingTransf.process(expr)

        # Add dynamic type checks.
        expr = dynamic.typeCheckTranslate(expr)

        # Dereference value references from the mapping.
        transf = valueref.ValueRefDereferencer()
        expr = transf.process(expr)

        # Simplify the expression
        expr = simplify.simplify(expr)

        # Convert select predicates to SQL
        expr = sqltranslate.translateSelectToSqlBool(expr)

        # Generate SQL.
        return emit.emit(expr)

    _versionIdPattern = re.compile('[0-9]')


    def getSink(self, graphUri=None, delete=False):
        # Get from mapping transform, if not set.
        if graphUri is None:
            try:
                graphUri = self.mappingTransf.getModifGraph()
            except NotImplementedError:
                raise ModifyError(_("Destination model is read-only"))

        # Return the appropriate sink.
        return SingleGraphRdfSink(self.modelBase, graphUri, delete=delete)

    def _processModifOp(self, expr):
        # Get the statement per row count before transforming to SQL.
        stmtsPerRow = len(expr[0]) - 1

        try:
            # Determine the type of operation we are executing.
            if isinstance(expr, nodes.Insert):
                delete = False
            elif isinstance(expr, nodes.Delete):
                delete = True
            else:
                assert False, "Unexpected expression type"

            # Process the data.
            self.modelBase.insertByQuery(self._exprToSql(expr[0]),
                                         stmtsPerRow)

            # Return count of affected rows
            return results.ModifResults(sink.rowsAffected)
        except:
            self.rollback()
            raise

    def query(self, queryLanguageOrTemplate, queryText=None,
              fileName=_("<unknown>"), **keywords):
        # Parse the query.
        queryObject = parsequery.parseQuery(queryLanguageOrTemplate,
                                            queryText, fileName=fileName,
                                            model=self, **self.modelArgs)
        expr = queryObject.expr

        # Flush the buffers in the model base in order to prevent the
        # query from producing invalid results due to unprocessed
        # data.
        self.modelBase.flush()

        if isinstance(expr, nodes.ModifOperation):
            return self._processModifOp(expr)

        # Find the main result mapping expression.
        mappingExpr = expr
        while not isinstance(mappingExpr, nodes.QueryResult):
            mappingExpr = mappingExpr[0]

        if mappingExpr.__class__ == nodes.MapResult:
            # Get the column names before transforming to SQL.
            columnNames = list(mappingExpr.columnNames)
            return ColumnResults(self._connection, columnNames,
                                 self._exprToSql(expr))
        elif mappingExpr.__class__ == nodes.StatementResult:
            # Get the statement count before transforming to SQL.
            stmtsPerRow = len(mappingExpr) - 1
            return StmtResults(self._connection, stmtsPerRow,
                               self._exprToSql(expr))
        elif mappingExpr.__class__ == nodes.ExistsResult:
            return ExistsResults(self._connection, self._exprToSql(expr))
        else:
            assert False, 'No mapping expression'

    def querySQL(self, queryLanguageOrTemplate, queryText=None,
              fileName=_("<unknown>"), **keywords):
        # Parse the query.
        queryObject = parsequery.parseQuery(queryLanguageOrTemplate,
                                            queryText, fileName=fileName,
                                            model=self, **self.modelArgs)
        expr = queryObject.expr

        if isinstance(expr, nodes.ModifOperation):
            return self._exprToSql(expr[0])
        else:
            return self._exprToSql(expr)

    def getPrefixes(self):
        return self.modelBase.getPrefixes()

    def close(self):
        self.modelBase = None


class TwoWayModel(BasicModel):

    __slots__ = ('prefixes')

    def __init__(self, modelBase, connection, mappingTransf, graphA, graphB, **modelArgs):
        super(TwoWayModel, self).__init__(modelBase, connection, mappingTransf, **modelArgs)

        self.prefixes = nsshortener.NamespaceUriShortener()
        self.prefixes.addPrefixes(modelBase.getPrefixes())

        graphAid = modelBase.lookupGraphId(graphA)
        graphBid = modelBase.lookupGraphId(graphB)

        # Won't be a problem, but won't give interesting results either
        assert graphAid != 0, "Graph A doesn't exist!"
        assert graphBid != 0, "Graph B doesn't exist!"

        graphUris = modelBase.prepareTwoWay(graphAid, graphBid)

        self.prefixes['compA'] = graphUris[0]
        self.prefixes['compB'] = graphUris[1]
        self.prefixes['compAB'] = graphUris[2]

    def getPrefixes(self):
        return self.prefixes

_modelFactories = {
    'plain': (BasicModel, GraphMapper),
    'twoway': (TwoWayModel, GraphMapper)
    }

def getModel(modelBase, connection, modelType, schema=None, **modelArgs):
    modelTypeNorm = modelType.lower()

    try:
        modelCls, transfCls = _modelFactories[modelTypeNorm]
    except KeyError:
        raise InstantiationError(_("Invalid model type '%s'") % modelType)
    except TypeError, e:
        raise InstantiationError(_("Missing or invalid model "
                                   "arguments: %s") % e)

    return modelCls(modelBase, connection,
                    transfCls(modelBase, **modelArgs),
                    **modelArgs)

def getModelMappers():
    mappers = {}
    for name, (factory, mapper) in _modelFactories.items():
        mappers[name] = mapper

    return mappers
