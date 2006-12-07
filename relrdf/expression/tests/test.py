import unittest

from relrdf.expression import nodes, evaluate
from relrdf.mapping import parseenv


class TestNodes(unittest.TestCase):

    __slots__ = ('env',)

    def setUp(self):
        self.env = parseenv.ParseEnvironment()

    def testLiteral(self):
        """Literals."""

        for exprTxt, val in (("true", True),
                             ("false", False),
                             ("5", 5),
                             ("5.3", 5.3),
                             ("3e+2", 3e+2),
                             ("'yeah'", 'yeah')):
            expr = self.env.parseExpr(exprTxt)
            self.assert_(isinstance(expr, nodes.Literal))
            self.assert_(evaluate.reduceToValue(expr) == val,
                         "Value for '%s' should be '%s'" %
                         (exprTxt, str(val)))


if __name__ == '__main__':
    unittest.main()
