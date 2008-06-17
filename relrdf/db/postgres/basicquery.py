import string
import re

import relrdf

from relrdf.localization import _
from relrdf.error import InstantiationError, ModifyError
from relrdf import results, mapping, parserfactory, commonns

from relrdf.typecheck import dynamic
from relrdf.expression import uri, literal, nodes, build, simplify
from relrdf.mapping import transform, valueref, sqlnodes, emit, sqltranslate

from relrdf.typecheck.typeexpr import LiteralType, BlankNodeType, \
     ResourceType, RdfNodeType, resourceType, rdfNodeType

def resourceTypeExpr():
    return nodes.Uri(commonns.rdfs.Resource)

class UriValueMapping(valueref.ValueMapping):
    """A value mapping capable of converting from arbitrary internal
    values to an external representation formed by prepending a base
    URI to the canonical string representation of the internal value."""

    __slots__ = ('baseUri',
                 'intToExtExpr',
                 'extToIntExpr')

    # Give this type of mapping priority in comparisons.
    weight = 80

    def __init__(self, baseUri):
        super(UriValueMapping, self).__init__()

        self.baseUri = baseUri

        self.intToExtExpr = 'CONCAT("%s", $0$)' % baseUri

        l = len(baseUri.encode('utf-8'))
        self.extToIntExpr = '''
        IF(SUBSTRING($0$, 1, %d) = "%s",
           SUBSTRING($0$, %d), "<<<NO VALUE>>>")''' % (l, baseUri, l + 1)

    def intToExt(self, internal):
        return sqlnodes.SqlScalarExpr(self.intToExtExpr, internal)

    def extToInt(self, expr):
        return sqlnodes.SqlScalarExpr(self.extToIntExpr, expr)


def uriValueRef(incarnation, fieldId, mapping):
    return valueref.ValueRef(mapping.copy(),
                             sqlnodes.SqlFieldRef(incarnation, fieldId))

class ChecksumValueMapping(valueref.ValueMapping):
    """A value mapping that uses a checksum column as internal
    representation, and a parallel text column as external
    representation. The checksum column is expected to contain a
    robust checksum (i.e., MD5) of the corresponding text value, so
    that it is possible to compare checksums instead of values, and
    still have a very low probability of false possitives.
    The internal expression must be a field reference pointing to the
    checksum field. The corresponding text field must be named by
    appending '_text' to the name of the checksum field."""

    __slots__ = ()

    def intToExt(self, internal):
        assert isinstance(internal, sqlnodes.SqlFieldRef)
        return sqlnodes.SqlFieldRef(internal.incarnation,
                                    internal.fieldId + '_text')

    def extToInt(self, expr):
        return sqlnodes.SqlScalarExpr('unhex(md5(convert($0$ using utf8)))',
                                      expr)


#def checksumValueRef(incarnation, fieldId):
#    return valueref.ValueRef(ChecksumValueMapping(),
#                             sqlnodes.SqlFieldRef(incarnation, fieldId))

class TypeUriMapping(valueref.ValueMapping):
    """A value mapping that uses type IDs as listed in the
    data_types SQL table instead of the full type URIs used
    by RDF"""
    
    __slots__ = ()
    
    def intToExt(self, internal):
        (expr,) = transform.Incarnator.reincarnate(nodes.MapValue(
                nodes.Select(
                     sqlnodes.SqlRelation(1, 'data_types'),
                     nodes.Equal(
                          sqlnodes.SqlFieldRef(1, 'id'),
                          nodes.Null()
                     )
                ),
                sqlnodes.SqlFieldRef(1, 'uri')
            ))    
        # Replace null by actual ID (done late so it won't reincarnate)
        assert isinstance(expr[0][1][1], nodes.Null)
        expr[0][1][1] = internal
        return expr
    
    def extToInt(self, external):
        (expr,) = transform.Incarnator.reincarnate(nodes.MapValue(
                nodes.Select(
                     sqlnodes.SqlRelation(1, 'data_types'),
                     nodes.Equal(
                          sqlnodes.SqlFieldRef(1, 'uri'),
                          nodes.Null()
                     )
                ),
                sqlnodes.SqlFieldRef(1, 'id')
            ))
        # Replace null by actual URI (done late so it won't reincarnate)
        assert isinstance(expr[0][1][1], nodes.Null)
        expr[0][1][1] = external
        return expr

def typeValueRef(incarnation, fieldId):
    
    valueExpr = sqlnodes.SqlFieldRef(incarnation, fieldId);
    typeIdExpr = sqlnodes.SqlFunctionCall('rdf_term_get_type_id', valueExpr)    
    
    return valueref.ValueRef(TypeUriMapping(), typeIdExpr)

class TextIdMapping(valueref.ValueMapping):
    
    __slots__ = ()
    
    def intToExt(self, internal):
        (expr,) = transform.Incarnator.reincarnate(nodes.MapValue(
                nodes.Select(
                     sqlnodes.SqlRelation(1, 'statement_text'),
                     nodes.Equal(
                          sqlnodes.SqlFieldRef(1, 'id'),
                          nodes.Null()
                     )
                ),
                sqlnodes.SqlFieldRef(1, 'txt')
            ))    
        # Replace null by actual ID (done late so it won't reincarnate)
        assert isinstance(expr[0][1][1], nodes.Null)
        expr[0][1][1] = internal
        return expr
    
    def extToInt(self, external):
        (expr,) = transform.Incarnator.reincarnate(nodes.MapValue(
                nodes.Select(
                     sqlnodes.SqlRelation(1, 'statement_text'),
                     nodes.Equal(
                          sqlnodes.SqlFieldRef(1, 'txt'),
                          nodes.Null()
                     )
                ),
                sqlnodes.SqlFieldRef(1, 'id')
            ))
        # Replace null by actual URI (done late so it won't reincarnate)
        assert isinstance(expr[0][1][1], nodes.Null)
        expr[0][1][1] = external
        return expr

def checksumValueRef(incarnation, fieldId):
    return sqlnodes.SqlFieldRef(incarnation, fieldId)
#    return valueref.ValueRef(TextIdMapping(),
#                             sqlnodes.SqlFieldRef(incarnation, fieldId))
    
class BasicMapper(transform.PureRelationalTransformer):
    """A base mapper for the MySQL basic schema. It handles the
    mapping of type expressions."""

    __slots__ = ()
                
    def mapTypeExpr(self, typeExpr):
        if isinstance(typeExpr, LiteralType):
            return nodes.Uri(commonns.rdfs.Literal)
        elif isinstance(typeExpr, ResourceType):
            return resourceTypeExpr()
        else:
            assert False, "Cannot determine type"

    canWrite = False
    """True iff this sink is able to write."""

    def insert(self, cursor, stmtQuery, stmtsPerRow):
        """Insert the statements returned by `stmtQuery` into the model."""
        raise NotImplementedError

    def delete(self, cursor, stmtQuery, stmtsPerRow):
        """Delete the statements returned by `stmtQuery` from the model."""
        raise NotImplementedError


class BasicSingleVersionMapper(BasicMapper):
    """Abstract class that targets an abstract query to a context set
    with only one element corresponding to a single version of a
    model. Reified patterns are not handled at all."""
    
    __slots__ = ('versionId',
                 'versionUri',

                 'versionMapping',
                 'stmtRepl')

    def __init__(self, versionId, versionUri):
        super(BasicSingleVersionMapper, self).__init__()

        self.versionId = int(versionId)
        self.versionUri = versionUri

        self.versionMapping = UriValueMapping(versionUri)

        # Cache for the statement pattern replacement expression.
        self.stmtRepl = None

    def replStatementPattern(self, expr):
        if self.stmtRepl is not None:
            return self.stmtRepl

        rel = build.buildExpression(
            (nodes.Select,
             (nodes.Product,
              (sqlnodes.SqlRelation, 1, 'version_statement'),
              (sqlnodes.SqlRelation, 2, 'statements')),
             (nodes.And,
              (nodes.Equal,
               (sqlnodes.SqlFieldRef, 1, 'version_id'),
               (sqlnodes.SqlInt, self.versionId)),
              (nodes.Equal,
               (sqlnodes.SqlFieldRef, 1, 'stmt_id'),
               (sqlnodes.SqlFieldRef, 2, 'id'))))
            )

        replExpr = \
          nodes.MapResult(['context', 'type__context',
                           'subject', 'type__subject',
                           'predicate', 'type__predicate',
                           'object', 'type__object'],
                          rel,
                          nodes.Uri(self.versionUri + str(self.versionId)),
                          resourceTypeExpr(),
                          checksumValueRef(2, 'subject'),
                          resourceTypeExpr(),
                          checksumValueRef(2, 'predicate'),
                          resourceTypeExpr(),
                          checksumValueRef(2, 'object'),
                          typeValueRef(2, 'object'))

        self.stmtRepl = (replExpr,
                         ('context', 'subject', 'predicate', 'object'))

        return self.stmtRepl


class SingleVersionMapper(BasicSingleVersionMapper,
                          transform.StandardReifTransformer):
    """Targets an abstract query to a context set with only one
    element corresponding to a single version of a model. Reified
    patterns are interpreted as four normal patterns in the standard
    RDFS fashion."""

    __slots__ = ()

    name = "Single Version"
    parameterInfo = ({"name":"versionId", "label":"Version ID", "tip":"Enter the ID of the version to be used", "assert":"versionId != ''", "asserterror":"Version ID must not be empty"},)

    def __init__(self, versionId, versionUri=commonns.relrdf.version):
        super(SingleVersionMapper, self).__init__(versionId,
                                                  versionUri)

    canWrite = True

    _stmtColsTmpl = string.Template(
        """
        hash$num binary(16),
        subject_text$num longtext NOT NULL,
        predicate_text$num longtext NOT NULL,
        object_type$num mediumint NOT NULL,
        object_text$num longtext NOT NULL
        """)

    _destColsTmpl = string.Template(
        """
        hash$num,
        subject_text$num,
        predicate_text$num,
        object_type$num,
        object_text$num
        """)

    _srcColsTmpl = string.Template(
        """
        unhex(md5(concat(sq.subject$num,
                         sq.predicate$num,
                         sq.object$num))),
        sq.subject$num,
        sq.predicate$num,
        sq.type__object$num,
        sq.object$num
        """)

    def _storeModifResults(self, cursor, stmtQuery, stmtsPerRow):
        """Run `stmtQuery` and store its results in a temporary
        table.
        """
        # FIXME: A bug/limitation in MySQL causes an automatic commit
        # whenever a table is dropped. To work around it, we use a
        # different table for each required width and reuse them as
        # needed.

        # Create (if it doesn't exist already) a temporary table to
        # hold the results.
        cursor.execute(
            """
            CREATE TEMPORARY TABLE IF NOT EXISTS statements_temp%d (%s)
              ENGINE=InnoDB DEFAULT CHARSET=utf8;
            """ %
            (stmtsPerRow,
             ', '.join((self._stmtColsTmpl.substitute(num=i+1)
                        for i in range(stmtsPerRow)))))

        # Clean up the table contents in case the table was already
        # there.
        cursor.execute(
            """
            DELETE FROM statements_temp%d
            """ % stmtsPerRow)

        # Write the statements into the table.
        cursor.execute(
            """
            INSERT INTO statements_temp%d (%s)
              SELECT %s FROM (%s) AS sq""" %
            (stmtsPerRow,
             ', '.join((self._destColsTmpl.substitute(num=i+1)
                        for i in range(stmtsPerRow))),
             ', '.join((self._srcColsTmpl.substitute(num=i+1)
                        for i in range(stmtsPerRow))),
             stmtQuery))

    _insertCreateStmts = string.Template(
        """
        INSERT INTO statements (hash, subject, predicate, object,
                                subject_text, predicate_text, object_type,
                                object_text)
          SELECT s.hash$num, unhex(md5(subject_text$num)),
                 unhex(md5(predicate_text$num)), unhex(md5(object_text$num)),
                 s.subject_text$num, s.predicate_text$num,
                 s.object_type$num, s.object_text$num
          FROM statements_temp$stmtsPerRow s
        ON DUPLICATE KEY UPDATE statements.subject = statements.subject;
        """)

    _insertAddToVersion = string.Template(
        """
        INSERT INTO version_statement (version_id, stmt_id)
          SELECT $versionId AS v_id, s.id
          FROM statements s, statements_temp$stmtsPerRow st
          WHERE s.hash = st.hash$num
        ON DUPLICATE KEY UPDATE version_id = $versionId;
        """)

    def insert(self, cursor, stmtQuery, stmtsPerRow):
        self._storeModifResults(cursor, stmtQuery, stmtsPerRow)

        count = 0
        for i in range(stmtsPerRow):
            # Put the statements into the table, without repetitions.
            cursor.execute(
                self._insertCreateStmts.substitute(num=i+1,
                                                   stmtsPerRow=stmtsPerRow))

            # Add the statement numbers to the version.
            cursor.execute(
                self._insertAddToVersion.substitute(versionId=self.versionId,
                                                    num=i+1,
                                                    stmtsPerRow=stmtsPerRow))
            count += cursor.rowcount

        return count

    _deleteRemoveFromVersion = string.Template(
        """
        DELETE FROM version_statement v
        USING version_statement v, statements s,
              statements_temp$stmtsPerRow st
        WHERE
          v.version_id = $versionId AND v.stmt_id = s.id AND
          s.hash = st.hash$num;
        """)

    def delete(self, cursor, stmtQuery, stmtsPerRow):
        self._storeModifResults(cursor, stmtQuery, stmtsPerRow)

        count = 0
        for i in range(stmtsPerRow):
            # Delete the statement numbers from the version.
            cursor.execute(
                self._deleteRemoveFromVersion.substitute(
                    versionId=self.versionId,
                    num=i+1,
                    stmtsPerRow=stmtsPerRow))
            count += cursor.rowcount

        return count


class AllVersionsMapper(BasicMapper,
                        transform.StandardReifTransformer):
    """Targets an abstract query to a context set whose elements are
    the versions of a model."""
    
    __slots__ = ('versionMapping',

                 'stmtRepl')
    name = "All Versions"
    parameterInfo = ()

    def __init__(self, versionUri=commonns.relrdf.version,
                 stmtUri=commonns.relrdf.stmt, metaInfoVersion=1):
        super(AllVersionsMapper, self).__init__()

        self.versionMapping = UriValueMapping(versionUri)

        # Cache for the statement pattern replacement expression.
        self.stmtRepl = None

    def replStatementPattern(self, expr):
        if self.stmtRepl is not None:
            return self.stmtRepl

        rel = build.buildExpression(
            (nodes.Select,
             (nodes.Product,
              (sqlnodes.SqlRelation, 1, 'version_statement'),
              (sqlnodes.SqlRelation, 2, 'statements')),
             (nodes.Equal,
              (sqlnodes.SqlFieldRef, 1, 'stmt_id'),
              (sqlnodes.SqlFieldRef, 2, 'id')))
            )

        replExpr = \
          nodes.MapResult(['context', 'type__context',
                           'subject', 'type__subject',
                           'predicate', 'type__predicate',
                           'object', 'type__object'],
                          rel,
                          uriValueRef(1, 'version_id', self.versionMapping),
                          resourceTypeExpr(),
                          checksumValueRef(2, 'subject'),
                          resourceTypeExpr(),
                          checksumValueRef(2, 'predicate'),
                          resourceTypeExpr(),
                          checksumValueRef(2, 'object'),
                          typeValueRef(2, 'object'))

        self.stmtRepl = (replExpr,
                         ('context', 'subject', 'predicate', 'object'))

        return self.stmtRepl


class AllStmtsMapper(BasicMapper,
                        transform.StandardReifTransformer):
    """Targets an abstract query to a context set with only one element
    containing the statements present in all versions of a model."""

    __slots__ = ('stmtRepl')

    name = "All statements"
    parameterInfo = ()

    def __init__(self):
        super(AllStmtsMapper, self).__init__()

        # Cache for the statement pattern replacement expression.
        self.stmtRepl = None

    def replStatementPattern(self, expr):
        if self.stmtRepl is not None:
            return self.stmtRepl

        rel = build.buildExpression((sqlnodes.SqlRelation, 1, 'statements'))

        replExpr = \
          nodes.MapResult(['context', 'type__context',
                           'subject', 'type__subject',
                           'predicate', 'type__predicate',
                           'object', 'type__object'],
                          rel,
                          nodes.Uri(commonns.relrdf.stmts),
                          resourceTypeExpr(),
                          checksumValueRef(1, 'subject'),
                          resourceTypeExpr(),
                          checksumValueRef(1, 'predicate'),
                          resourceTypeExpr(),
                          checksumValueRef(1, 'object'),
                          typeValueRef(1, 'object'))

        self.stmtRepl = (replExpr,
                         ('context', 'subject', 'predicate', 'object'))

        return self.stmtRepl


class MetaVersionMapper(BasicSingleVersionMapper,
                        transform.MatchReifTransformer):
    """Targets an abstract query to a context with only one element
    corresponding to version 1 of a model (the meta-information
    version). Reified patterns will match statements present in all
    model versions. A special relation relrdf:versionContainsStmt can
    be used to determine which statements are in which version."""

    __slots__ = ('stmtUri',

                 'stmtMapping',
                 'reifStmtRepl')
                 
    name = "Meta Version"
    parameterInfo = ()

    def __init__(self, versionUri=commonns.relrdf.version,
                 stmtUri=commonns.relrdf.stmt):
        super(MetaVersionMapper, self).__init__(1, versionUri)

        self.stmtUri = stmtUri

        self.stmtMapping = UriValueMapping(stmtUri)

        # Cache for the reified statement pattern replacement expression.
        self.reifStmtRepl = None

    def replStatementPattern(self, expr):
        replExpr = None

        if isinstance(expr[2], nodes.Uri) and \
           expr[2].uri == commonns.rdf.type and \
           isinstance(expr[3], nodes.Uri) and \
           expr[3].uri == commonns.rdf.Statement:
            rel = sqlnodes.SqlRelation(1, 'statements')
            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              nodes.Uri(self.versionUri + '1'),
                              resourceTypeExpr(),
                              uriValueRef(1, 'id', self.stmtMapping),
                              resourceTypeExpr(),
                              nodes.Literal(commonns.rdf.type),
                              resourceTypeExpr(),
                              nodes.Literal(commonns.rdf.Statement),
                              resourceTypeExpr())
        elif isinstance(expr[2], nodes.Uri) and \
             expr[2].uri == commonns.relrdf.versionContainsStmt:
            rel = sqlnodes.SqlRelation(1, 'version_statement')
            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              nodes.Uri(self.versionUri + '1'),
                              resourceTypeExpr(),
                              uriValueRef(1, 'version_id',
                                          self.versionMapping),
                              resourceTypeExpr(),
                              nodes.Literal(commonns.relrdf. \
                                            versionContainsStmt),
                              resourceTypeExpr(),
                              uriValueRef(1, 'stmt_id', self.stmtMapping),
                              resourceTypeExpr())
        elif isinstance(expr[2], nodes.Uri) and \
             expr[2].uri == commonns.rdf.subject:
            rel = sqlnodes.SqlRelation(1, 'statements')
            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              nodes.Uri(self.versionUri + '1'),
                              resourceTypeExpr(),
                              uriValueRef(1, 'id', self.stmtMapping),
                              resourceTypeExpr(),
                              nodes.Literal(commonns.rdf.subject),
                              resourceTypeExpr(),
                              checksumValueRef(1, 'subject'),
                              resourceTypeExpr())
        elif isinstance(expr[2], nodes.Uri) and \
             expr[2].uri == commonns.rdf.predicate:
            rel = sqlnodes.SqlRelation(1, 'statements')
            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              nodes.Uri(self.versionUri + '1'),
                              resourceTypeExpr(),
                              uriValueRef(1, 'id', self.stmtMapping),
                              resourceTypeExpr(),
                              nodes.Literal(commonns.rdf.predicate),
                              resourceTypeExpr(),
                              checksumValueRef(1, 'predicate'),
                              resourceTypeExpr())
        elif isinstance(expr[2], nodes.Uri) and \
             expr[2].uri == commonns.rdf.object:
            rel = sqlnodes.SqlRelation(1, 'statements')
            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              nodes.Uri(self.versionUri + '1'),
                              resourceTypeExpr(),
                              uriValueRef(1, 'id', self.stmtMapping),
                              resourceTypeExpr(),
                              nodes.Literal(commonns.rdf.object),
                              resourceTypeExpr(),
                              checksumValueRef(1, 'object'),
                              typeValueRef(1, 'object'))

        if replExpr is not None:
            return (replExpr,
                    ('context', 'subject', 'predicate', 'object'))
        else:
            return super(MetaVersionMapper, self).replStatementPattern(expr)

    def replReifStmtPattern(self, expr):
        if self.reifStmtRepl is not None:
            return self.reifStmtRepl

        rel = sqlnodes.SqlRelation(1, 'statements')

        replExpr = \
          nodes.MapResult(['context', 'type__context',
                           'stmt', 'type__stmt',
                           'subject', 'type__subject',
                           'predicate', 'type__predicate',
                           'object', 'type__object'],
                          rel,
                          nodes.Uri(self.versionUri + '1'),
                          resourceTypeExpr(),
                          uriValueRef(1, 'id', self.stmtMapping),
                          resourceTypeExpr(),
                          checksumValueRef(1, 'subject'),
                          resourceTypeExpr(),
                          checksumValueRef(1, 'predicate'),
                          resourceTypeExpr(),
                          checksumValueRef(1, 'object'),
                          typeValueReff(1, 'object'))

        self.reifStmtRepl = (replExpr,
            ('context', 'stmt', 'subject', 'predicate', 'object'))

        return self.reifStmtRepl


compMapping = UriValueMapping(commonns.relrdf.comp)


class TwoWayComparisonMapper(BasicMapper,
                             transform.StandardReifTransformer):
    """Targets an abstract query to a context set presenting two
    versions (versions A and B) as three contexts: one containing the
    statements only in A, one containing the statements only in B, and
    one containing the statements common to both versions."""
    
    __slots__ = ('versionA',
                 'versionB',
                 'refreshComp',

                 'stmtRepl',)

    name = "Two Way Comparision"
    parameterInfo = ({"name":"versionA", "label":"Version A", "tip":"Enter version 1 to compare", "assert":"versionA!=''", "asserterror":"Version must not be empty"},
                     {"name":"versionB", "label":"Version B", "tip":"Enter version 2 to compare", "assert":"versionB!=''", "asserterror":"Version must not be empty"})

    def __init__(self, versionA, versionB, refreshComp=0):

        super(TwoWayComparisonMapper, self).__init__()

        self.versionA = int(versionA)
        self.versionB = int(versionB)
        self.refreshComp = int(refreshComp) != 0

        # Cache for the statement pattern replacement expression.
        self.stmtRepl = None

    def replStatementPattern(self, expr):
        # Check for complete version matching.
        if isinstance(expr[0], nodes.Uri) and \
               expr[0].uri.startswith(commonns.relrdf.model) and \
               len(expr[0].uri) == len(commonns.relrdf.model) + 1 and \
               expr[0].uri[len(commonns.relrdf.model)] in ('A', 'B'):
            modelLetter = expr[0].uri[len(commonns.relrdf.model)]
            if modelLetter == 'A':
                versionId = self.versionA
            else:
                versionId = self.versionB

            rel = build.buildExpression(
                (nodes.Select,
                 (nodes.Product,
                  (sqlnodes.SqlRelation, 1, 'version_statement'),
                  (sqlnodes.SqlRelation, 2, 'statements')),
                 (nodes.And,
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'version_id'),
                   (nodes.Literal, versionId)),
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'stmt_id'),
                   (sqlnodes.SqlFieldRef, 2, 'id'))))
                )

            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              nodes.Uri(commonns.relrdf.model + modelLetter),
                              resourceTypeExpr(),
                              checksumValueRef(2, 'subject'),
                              resourceTypeExpr(),
                              checksumValueRef(2, 'predicate'),
                              resourceTypeExpr(),
                              checksumValueRef(2, 'object'),
                              typeValueRef(2, 'object'))
        else:
            rel = build.buildExpression(
                (nodes.Select,
                 (nodes.Product,
                  (sqlnodes.SqlRelation, 1, 'twoway'),
                  (sqlnodes.SqlRelation, 2, 'statements')),
                 (nodes.And,
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'version_a'),
                   (nodes.Literal, self.versionA)),
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'version_b'),
                   (nodes.Literal, self.versionB)),
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'stmt_id'),
                   (sqlnodes.SqlFieldRef, 2, 'id'))))
                )

            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              uriValueRef(1, 'context', compMapping),
                              resourceTypeExpr(),
                              checksumValueRef(2, 'subject'),
                              resourceTypeExpr(),
                              checksumValueRef(2, 'predicate'),
                              resourceTypeExpr(),
                              checksumValueRef(2, 'object'),
                              typeValueRef(2, 'object'))

        return (replExpr,
                ('context', 'subject', 'predicate', 'object'))


class ThreeWayComparisonMapper(BasicMapper,
                               transform.StandardReifTransformer):
    """Targets an abstract query to a context set presenting three
    versions (versions A, B and C) as seven contexts, corresponding to
    all combinations of being in A, B, and/or C."""
    
    __slots__ = ('versionA',
                 'versionB',
                 'versionC',
                 'refreshComp',

                 'stmtRepl',)

    name = "Three Way Comparision"
    parameterInfo = ({"name":"versionA", "label":"Version A", "tip":"Enter version 1 to compare", "assert":"versionA!=''", "asserterror":"Version must not be empty"},
                     {"name":"versionB", "label":"Version B", "tip":"Enter version 2 to compare", "assert":"versionB!=''", "asserterror":"Version must not be empty"},
                     {"name":"versionC", "label":"Version C", "tip":"Enter version 3 to compare", "assert":"versionC!=''", "asserterror":"Version must not be empty"})

    def __init__(self, versionA, versionB, versionC, refreshComp=0):
        super(ThreeWayComparisonMapper, self).__init__()

        self.versionA = int(versionA)
        self.versionB = int(versionB)
        self.versionC = int(versionC)
        self.refreshComp = int(refreshComp) != 0

        # Cache for the statement pattern replacement expression.
        self.stmtRepl = None

    def replStatementPattern(self, expr):
        # Check for complete version matching.
        if isinstance(expr[0], nodes.Uri) and \
               expr[0].uri.startswith(commonns.relrdf.model) and \
               len(expr[0].uri) == len(commonns.relrdf.model) + 1 and \
               expr[0].uri[len(commonns.relrdf.model)] in ('A', 'B', 'C'):
            modelLetter = expr[0].uri[len(commonns.relrdf.model)]
            if modelLetter == 'A':
                versionId = self.versionA
            elif modelLetter == 'B':
                versionId = self.versionB
            else:
                versionId = self.versionC

            rel = build.buildExpression(
                (nodes.Select,
                 (nodes.Product,
                  (sqlnodes.SqlRelation, 1, 'version_statement'),
                  (sqlnodes.SqlRelation, 2, 'statements')),
                 (nodes.And,
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'version_id'),
                   (nodes.Literal, versionId)),
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'stmt_id'),
                   (sqlnodes.SqlFieldRef, 2, 'id'))))
                )

            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              nodes.Uri(commonns.relrdf.model + modelLetter),
                              resourceTypeExpr(),
                              checksumValueRef(2, 'subject'),
                              resourceTypeExpr(),
                              checksumValueRef(2, 'predicate'),
                              resourceTypeExpr(),
                              checksumValueRef(2, 'object'),
                              typeValueRef(2, 'object'))
        else:
            rel = build.buildExpression(
                (nodes.Select,
                 (nodes.Product,
                  (sqlnodes.SqlRelation, 1, 'threeway'),
                  (sqlnodes.SqlRelation, 2, 'statements')),
                 (nodes.And,
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'version_a'),
                   (nodes.Literal, self.versionA)),
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'version_b'),
                   (nodes.Literal, self.versionB)),
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'version_c'),
                   (nodes.Literal, self.versionC)),
                  (nodes.Equal,
                   (sqlnodes.SqlFieldRef, 1, 'stmt_id'),
                   (sqlnodes.SqlFieldRef, 2, 'id'))))
                )

            replExpr = \
              nodes.MapResult(['context', 'type__context',
                               'subject', 'type__subject',
                               'predicate', 'type__predicate',
                               'object', 'type__object'],
                              rel,
                              uriValueRef(1, 'context', compMapping),
                              resourceTypeExpr(),
                              checksumValueRef(2, 'subject'),
                              resourceTypeExpr(),
                              checksumValueRef(2, 'predicate'),
                              resourceTypeExpr(),
                              checksumValueRef(2, 'object'),
                              typeValueRef(2, 'object'))

        return (replExpr,
                ('context', 'subject', 'predicate', 'object'))


class BaseResults(object):
    __slots__ = ('cursor',
                 'length',)

    def __init__(self, connection, sqlText):
        self.cursor = connection.cursor()

        # Send the query to the database (iterating on this object
        # will produce the actual results.)
        self.cursor.execute(sqlText)

        self.length = self.cursor.rowcount

    def resultType(self):
        return NotImplemented

    def __len__(self):
        return self.length

    def _convertResult(self, rawValue, typeId, blankMap):
        if isinstance(rawValue, str):
            try:
                rawValue = rawValue.decode('utf8')
            except UnicodeDecodeError:
                rawValue = "<<Character encoding error>>"

        if rawValue is None:
            value = None
        elif typeId == commonns.rdfs.Resource:
            value = uri.Uri(rawValue)
            
            # Needs reinstantiation?
            if value.isBlank() and value.endswith('#reinst'):
                try:
                    value = blankMap[rawValue]
                except KeyError:
                    value = blankMap[rawValue] = uri.newBlank()
            
        elif typeId == commonns.rdfs.Literal:
            value = literal.Literal(rawValue)
        else:
            # Expect everything that's not a resource to be some
            # sort of literal
            value = literal.Literal(rawValue, typeId)
        
        return value

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
            for rawValue, typeId in zip(row[0::2], row[1::2]):
                result.append(self._convertResult(rawValue, typeId, blankMap))
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
                for rawValue, typeId in zip(row[i*6 : (i+1)*6 : 2],
                                            row[i*6 + 1: (i+1)*6 + 1: 2]):
                    result.append(self._convertResult(rawValue, typeId, blankMap))
                yield tuple(result)

            row = self.cursor.fetchone()

        self.close()

    __iter__ = iterAll


class BasicModel(object):
    __slots__ = ('modelBase',
                 'mappingTransf',
                 'modelArgs',
                 '_connection',
                 '_changeCursor',)

    def __init__(self, modelBase, mappingTransf, **modelArgs):
        self.modelBase = modelBase
        self.mappingTransf = mappingTransf
        self.modelArgs = modelArgs

        # Add the prefixes from the model base to modelArgs, so that
        # the parser receives them.
        paramPrf = modelArgs.get('prefixes', {})
        for prefix, namespace in modelBase.getPrefixes().items():
            paramPrf[prefix] = uri.Namespace(namespace)
        modelArgs['prefixes'] = paramPrf

        # Connections are created when a transaction is started.
        self._connection = None

        # The change cursor is initialized when actual changes are in
        # progress.
        self._changeCursor = None

    def _startTransaction(self):
        assert self._connection is None

        self._connection = self.modelBase.createConnection()

    def _exprToSql(self, expr):
        
        # Add explicit type columns to results.
        transf = transform.ExplicitTypeTransformer()
        expr = transf.process(expr)
        print expr

        # Apply the selected mapping.
        expr = self.mappingTransf.process(expr)
        print expr
        
        # Add dynamic type checks.
        expr = dynamic.dynTypeCheckTranslate(expr)
        print expr

        # Dereference value references from the mapping.
        transf = valueref.ValueRefDereferencer()
        expr = transf.process(expr)
        print expr
        
        # Simplify the expression
        expr = simplify.simplify(expr)
        print expr

        # Convert select predicates to SQL
        expr = sqltranslate.translateSelectToSqlBool(expr)
        print expr
        
        # Generate SQL.
        return emit.emit(expr)

    _versionIdPattern = re.compile('[0-9]')

    def _processModifOp(self, expr):
        if expr.graphUri is None:
            mappingTransf = self.mappingTransf
        else:
            # FIXME: This should probably be done through the model
            # factory.
            
            # Find a suitable version URI.
            if hasattr(self.mappingTransf, 'versionUri'):
                versionUri = self.mappingTransf.versionUri
            else:
                versionUri = commonns.relrdf.version

            if not expr.graphUri.startswith(versionUri):
                raise ModifyError(_("%s is not a valid model URI") %
                                  expr.graphUri)

            versionId = expr.graphUri[len(versionUri):]
            if self._versionIdPattern.match(versionId) is None:
                raise ModifyError(_("'%s' is not a valid version identifier") %
                                  versionId)

            mappingTransf = SingleVersionMapper(int(versionId), versionUri)

        if not mappingTransf.canWrite:
            raise ModifyError(_("Destination model is read-only"))

        # Get the statement per row count before transforming to SQL.
        stmtsPerRow = len(expr[0]) - 1

        try:
            if self._changeCursor is None:
                self._changeCursor = self._connection.cursor()

            if isinstance(expr, nodes.Insert):
                return results.ModifResults(
                    mappingTransf.insert(self._changeCursor,
                                         self._exprToSql(expr[0]),
                                         stmtsPerRow))
            elif isinstance(expr, nodes.Delete):
                return results.ModifResults(
                    mappingTransf.delete(self._changeCursor,
                                         self._exprToSql(expr[0]),
                                         stmtsPerRow))
            else:
                assert False, "Unexpected expression type"
        except:
            self.rollback()
            raise

    def query(self, queryLanguageOrTemplate, queryText=None,
              fileName=_("<unknown>"), **keywords):
        # FIXME: This code should be in a generic superclass.
        if queryText is None:
            # We should have been called with a template.
            template = queryLanguageOrTemplate
            assert hasattr(template, 'substitute')
            assert callable(template.substitute)

            # Expand the template:
            queryLanguage = template.queryLanguage
            queryText = template.substitute(keywords)
        else:
            queryLanguage = queryLanguageOrTemplate

            if len(keywords) > 0:
                # Treat the queryText as a template.
                template = relrdf.makeTemplate(queryLanguage, queryText)
                queryText = template.substitute(keywords)

        if self._connection is None:
            # Start a transaction:
            self._startTransaction()

        # Parse the query.
        parser = parserfactory.getQueryParser(queryLanguage,
                                              **self.modelArgs)
        expr = parser.parse(queryText, fileName)

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
        else:
            assert False, 'No mapping expression'

    def commit(self):
        if self._connection is None:
            return

        self._connection.commit()
        self._changeCursor = None
        self._connection.close()
        self._connection = None

    def rollback(self):
        if self._connection is None:
            return

        self._connection.rollback()
        self._changeCursor = None
        self._connection.close()
        self._connection = None

    def getPrefixes(self):
        return self.modelBase.getPrefixes()

    def close(self):
        self.rollback()

    def __del__(self):
        self.close()


class TwoWayModel(BasicModel):
    __slots__ = ('versionA',
                 'versionB',
                 'refreshComp',)

    def __init__(self, modelBase, mappingTransf, versionA, versionB,
                 refreshComp=0):
        super(TwoWayModel, self).__init__(modelBase, mappingTransf,
                                          versionA=versionA,
                                          versionB=versionB,
                                          refreshComp=refreshComp)

        self.versionA = int(versionA)
        self.versionB = int(versionB)
        self.refreshComp = int(refreshComp) != 0

        self.modelBase.prepareTwoWay(self.versionA, self.versionB,
                                     self.refreshComp)

    def close(self):
        self.modelBase.releaseTwoWay(self.versionA, self.versionB)

        super(TwoWayModel, self).close()


class ThreeWayModel(BasicModel):
    __slots__ = ('versionA',
                 'versionB',
                 'versionC',
                 'refreshComp',)

    def __init__(self, modelBase, mappingTransf, versionA, versionB,
                 versionC, refreshComp=0):
        super(ThreeWayModel, self).__init__(modelBase, mappingTransf,
                                            versionA=versionA,
                                            versionB=versionB,
                                            versionC=versionC,
                                            refreshComp=refreshComp)

        self.versionA = int(versionA)
        self.versionB = int(versionB)
        self.versionC = int(versionC)
        self.refreshComp = int(refreshComp) != 0

        self.modelBase.prepareThreeWay(self.versionA, self.versionB,
                                       self.versionC, self.refreshComp)

    def close(self):
        self.modelBase.releaseThreeWay(self.versionA, self.versionB,
                                       self.versionC)

        super(ThreeWayModel, self).close()


_modelFactories = {
    'metaversion': (BasicModel, MetaVersionMapper),
    'singleversion': (BasicModel, SingleVersionMapper),
    'allversions': (BasicModel, AllVersionsMapper),
    'allstatements': (BasicModel, AllStmtsMapper),
    'twoway': (TwoWayModel, TwoWayComparisonMapper),
    'threeway': (ThreeWayModel, ThreeWayComparisonMapper),
    }

def getModel(modelBase, modelType, schema=None, **modelArgs):
    modelTypeNorm = modelType.lower()

    if schema is not None:
        # Try to load the schema.
        schema = mapping.loadSchema(schema)
        if schema is None:
            raise InstantiationError(_("Schema '%s' not found") % schema)

        transf = schema.getMapper(modelType, **modelArgs)
    else:
        try:
            modelCls, transfCls = _modelFactories[modelTypeNorm]
        except KeyError:
            raise InstantiationError(_("Invalid model type '%s'") % modelType)
        except TypeError, e:
            raise InstantiationError(_("Missing or invalid model "
                                       "arguments: %s") % e)

    return modelCls(modelBase, transfCls(**modelArgs), **modelArgs)

def getModelMappers():
    mappers = {}
    for name, (factory, mapper) in _modelFactories.items():
        mappers[name] = mapper

    return mappers
