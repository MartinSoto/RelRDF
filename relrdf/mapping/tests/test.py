import unittest

from relrdf.expression import nodes
from relrdf.mapping import sqlnodes, environment


class TestSchema(unittest.TestCase):

    __slots__ = ('env',
                 'schema')

    def setUp(self):
        self.env = environment.ParseEnvironment()
        self.schema = None

    def tearDown(self):
        self.env = None
        self.schema = None

    def loadSchema(self, name):
        fileName = '%s.schema' % name
        stream = file(fileName)
        self.schema = self.env.parse(stream, fileName)

    def testSimpleMappingMatch(self):
        """Test simple positional mapping pattern matching for cases
        where patterns match."""

        self.loadSchema('simple-mapping-matching')
        mapper = self.schema.getMapper('testMapping')
        qPattern = nodes.StatementPattern(nodes.Var('a'),
                                          nodes.Var('b'),
                                          nodes.Var('c'),
                                          nodes.Var('d'))

        for i in range(4):
            expr = qPattern.copy()
            expr[i] = nodes.Uri('http://xxx%d' % i)
            expr = mapper.replStatementPattern(expr)

            self.assert_(isinstance(expr, sqlnodes.SqlRelation))
            self.assert_(expr.sqlCode == 'tab%d' % i)

        expr = qPattern.copy()
        expr[1] = nodes.Uri('http://xxx1')
        expr[3] = nodes.Uri('http://xxx3')
        expr = mapper.replStatementPattern(expr)
        expr.prettyPrint()
        self.assert_(isinstance(expr, sqlnodes.SqlRelation))
        self.assert_(expr.sqlCode == 'tab4')

        # Not matching cases:

        expr = mapper.replStatementPattern(qPattern)
        self.assert_(isinstance(expr, sqlnodes.SqlRelation))
        self.assert_(expr.sqlCode == 'tabDefault')

        qPattern = nodes.StatementPattern(nodes.Uri('http://xxxy'),
                                          nodes.Uri('http://xxxy'),
                                          nodes.Uri('http://xxxy'),
                                          nodes.Uri('http://xxxy'))
        expr = mapper.replStatementPattern(qPattern)
        self.assert_(isinstance(expr, sqlnodes.SqlRelation))
        self.assert_(expr.sqlCode == 'tabDefault')

    def testSimpleMappingParam(self):
        """Test mapping parameters."""

        self.loadSchema('simple-mapping-param')
        mapper = self.schema.getMapper('testMapping',
                                       sb1='http://sb1',
                                       sb2='http://sb2')
    
        qPattern = nodes.StatementPattern(nodes.Var('a'),
                                          nodes.Var('b'),
                                          nodes.Var('c'),
                                          nodes.Var('d'))

        for uri, tab in (('http://sb1', 'tab1'),
                         ('http://sb2', 'tab2'),
                         ('http://sb3', 'tabDefault')):
            expr = qPattern.copy()
            expr[1] = nodes.Uri(uri)
            expr = mapper.replStatementPattern(expr)
            self.assert_(isinstance(expr, sqlnodes.SqlRelation))
            self.assert_(expr.sqlCode == tab)


if __name__ == '__main__':
    unittest.main()
