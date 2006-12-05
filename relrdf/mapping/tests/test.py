import unittest

# PyUnit's asserRaise seems to need that exceptions are imported into
# the namespace.
from relrdf.error import SchemaError

from relrdf.expression import nodes
from relrdf.mapping import sqlnodes, environment


class TestSchema(unittest.TestCase):

    __slots__ = ('env',
                 'schema',
                 'qpattern')

    def setUp(self):
        self.env = environment.ParseEnvironment()
        self.schema = None
        self.qPattern = nodes.StatementPattern(nodes.Uri('http://xxxy'),
                                               nodes.Uri('http://xxxy'),
                                               nodes.Uri('http://xxxy'),
                                               nodes.Uri('http://xxxy'))

    def loadSchema(self, name):
        fileName = '%s.schema' % name
        stream = file(fileName)
        self.schema = self.env.parse(stream, fileName)

    def testSimpleMappingMatch(self):
        """Test simple positional mapping pattern matching for cases
        where patterns match."""

        self.loadSchema('simple-mapping-matching')
        mapper = self.schema.getMapper('testMapping')

        for i in range(4):
            expr = self.qPattern.copy()
            expr[i] = nodes.Uri('http://xxx%d' % i)
            expr = mapper.replStatementPattern(expr)

            self.assert_(isinstance(expr, sqlnodes.SqlRelation))
            self.assert_(expr.sqlCode == 'tab%d' % i)

        expr = self.qPattern.copy()
        expr[1] = nodes.Uri('http://xxx1')
        expr[3] = nodes.Uri('http://xxx3')
        expr = mapper.replStatementPattern(expr)
        self.assert_(isinstance(expr, sqlnodes.SqlRelation))
        self.assert_(expr.sqlCode == 'tab4')

        # Not matching cases:

        expr = mapper.replStatementPattern(self.qPattern)
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
    
        for uri, tab in (('http://sb1', 'tab1'),
                         ('http://sb2', 'tab2'),
                         ('http://sb3', 'tabDefault')):
            expr = self.qPattern.copy()
            expr[1] = nodes.Uri(uri)
            expr = mapper.replStatementPattern(expr)
            self.assert_(isinstance(expr, sqlnodes.SqlRelation))
            self.assert_(expr.sqlCode == tab)

    def testMappingCondNoReduceError(self):
        """Test for exception when a mapping condition cannot be
        reduced."""

        self.loadSchema('mapping-cond-no-reduce-error')
        mapper = self.schema.getMapper('testMapping')

        self.assertRaises(SchemaError, mapper.replStatementPattern,
                          self.qPattern)

    def testSimpleMacro(self):
        """Test simple macro definitions."""

        self.loadSchema('simple-macro')
        mapper = self.schema.getMapper('testMapping')

        for uri, tab in (('http://xxx1', 'tab1'),
                         ('http://xxx2', 'tabDefault')):
            expr = self.qPattern.copy()
            expr[1] = nodes.Uri(uri)
            expr = mapper.replStatementPattern(expr)
            self.assert_(isinstance(expr, sqlnodes.SqlRelation))
            self.assert_(expr.sqlCode == tab)

if __name__ == '__main__':
    unittest.main()
