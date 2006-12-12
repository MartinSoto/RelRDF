import unittest

# PyUnit's assertRaise seems to require exceptions to be imported into
# the namespace (i.e., importing just the error module doesn't work.)
from relrdf.error import SchemaError

from relrdf.expression import nodes
from relrdf.mapping import sqlnodes, sqleval, parseenv, valueref


class TestSchema(unittest.TestCase):

    __slots__ = ('env',
                 'schema',
                 'qpattern')

    def setUp(self):
        self.env = parseenv.ParseEnvironment()
        self.schema = None
        self.qPattern = nodes.StatementPattern(nodes.Uri('http://xxxy'),
                                               nodes.Uri('http://xxxy'),
                                               nodes.Uri('http://xxxy'),
                                               nodes.Uri('http://xxxy'))

    def loadSchema(self, name):
        fileName = '%s.schema' % name
        stream = file(fileName)
        self.schema = self.env.parseSchema(stream, fileName)

    def testParse(self):
        """Parse a complete schema."""
        self.loadSchema('basic')

    def testSimpleMappingMatch(self):
        """Simple positional mapping pattern matching."""

        self.loadSchema('simple-mapping-matching')
        mapper = self.schema.getMapper('testMapping')

        for i in range(4):
            expr = self.qPattern.copy()
            expr[i] = nodes.Uri('http://xxx%d' % i)
            expr = mapper.replStatementPattern(expr)[0]

            self.assert_(isinstance(expr, sqlnodes.SqlRelation))
            self.assert_(expr.sqlCode == 'tab%d' % i)

        expr = self.qPattern.copy()
        expr[1] = nodes.Uri('http://xxx1')
        expr[3] = nodes.Uri('http://xxx3')
        expr = mapper.replStatementPattern(expr)[0]
        self.assert_(isinstance(expr, sqlnodes.SqlRelation))
        self.assert_(expr.sqlCode == 'tab4')

        # Not matching cases:

        expr = mapper.replStatementPattern(self.qPattern)[0]
        self.assert_(isinstance(expr, sqlnodes.SqlRelation))
        self.assert_(expr.sqlCode == 'tabDefault')

        qPattern = nodes.StatementPattern(nodes.Uri('http://xxxy'),
                                          nodes.Uri('http://xxxy'),
                                          nodes.Uri('http://xxxy'),
                                          nodes.Uri('http://xxxy'))
        expr = mapper.replStatementPattern(qPattern)[0]
        self.assert_(isinstance(expr, sqlnodes.SqlRelation))
        self.assert_(expr.sqlCode == 'tabDefault')

    def testSimpleMappingParam(self):
        """Mapping parameters."""

        self.loadSchema('simple-mapping-param')
        mapper = self.schema.getMapper('testMapping',
                                       sb1='http://sb1',
                                       sb2='http://sb2')
    
        for uri, tab in (('http://sb1', 'tab1'),
                         ('http://sb2', 'tab2'),
                         ('http://sb3', 'tabDefault')):
            expr = self.qPattern.copy()
            expr[1] = nodes.Uri(uri)
            expr = mapper.replStatementPattern(expr)[0]
            self.assert_(isinstance(expr, sqlnodes.SqlRelation))
            self.assert_(expr.sqlCode == tab)

    def testMappingCondNoReduceError(self):
        """Exception when a mapping condition cannot be reduced."""

        self.loadSchema('mapping-cond-no-reduce-error')
        mapper = self.schema.getMapper('testMapping')

        self.assertRaises(SchemaError, mapper.replStatementPattern,
                          self.qPattern)

    def testSimpleMacro(self):
        """Simple macro definitions."""

        self.loadSchema('simple-macro')
        mapper = self.schema.getMapper('testMapping')

        for uri, tab in (('http://xxx1', 'tab1'),
                         ('http://xxx2', 'tabDefault')):
            expr = self.qPattern.copy()
            expr[1] = nodes.Uri(uri)
            expr = mapper.replStatementPattern(expr)[0]
            self.assert_(isinstance(expr, sqlnodes.SqlRelation))
            self.assert_(expr.sqlCode == tab)

    def testSimpleValueMapping(self):
        """Simple value mapping definitions."""

        self.loadSchema('simple-value-mapping')
        mapper = self.schema.getMapper('singleVersion', versionId=3)
        expr = mapper.replStatementPattern(self.qPattern)[0]

        self.assert_(isinstance(expr[1], valueref.ValueRef))
        self.assert_(isinstance(expr[1][0], valueref.MacroValueMapping))
        self.assert_(expr[1][0][0].params == ['int'])
        self.assert_(expr[1][0][1].params == ['ext'])


class TestSqlFunctions(unittest.TestCase):

    __slots__ = ('env',)

    def setUp(self):
        self.env = parseenv.ParseEnvironment()

    def testFunctioNoEval(self):
        """Expressions with function that cannot be reduced."""

        expr = self.env.parseExpr("kkqq(1, 2)")
        self.assert_(sqleval.reduceToValue(expr) is None)

        expr = self.env.parseExpr("substr($a, 1, 2)")
        self.assert_(sqleval.reduceToValue(expr) is None)

    def testStringFunctions(self):
        """Substr function."""

        for exprTxt, val in (("len('abcd')", 4),
                             ("substr('abcd', 1, 2)", 'ab'),):
            expr = self.env.parseExpr(exprTxt)
            self.assert_(isinstance(expr, sqlnodes.SqlFunctionCall))
            real = sqleval.reduceToValue(expr)
            self.assert_(real == val,
                         "Value for '%s' should be '%s' (was '%s')" %
                         (exprTxt, str(val), str(real)))


if __name__ == '__main__':
    unittest.main()
