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
                             ("'yeah'", 'yeah'),):
            expr = self.env.parseExpr(exprTxt)
            self.assert_(isinstance(expr, nodes.Literal))
            real = evaluate.reduceToValue(expr)
            self.assert_(real == val,
                         "Value for '%s' should be '%s' (was '%s')" %
                         (exprTxt, str(val), str(real)))

    def testArithmetic(self):
        """Arithmetic expressions."""

        for exprTxt, val in (("1 + 2", 3),
                             ("3.5 + 4", 7.5),
                             ("-3 + 2", -1),
                             ("3 - 2", 1),
                             ("7-3 -2", 2),
                             ("-10-(3+2)", -15),
                             ("2*4", 8),
                             ("2.5 * 4", 10),
                             ("10 / 4", 2.5),
                             ("10 / 2.5", 4),
                             ("3 + 2*5", 13),
                             ("(3 + 2) * 5", 25),):
            expr = self.env.parseExpr(exprTxt)
            self.assert_(isinstance(expr, nodes.ArithmeticOperation))
            real = evaluate.reduceToValue(expr)
            self.assert_(real == val,
                         "Value for '%s' should be '%s' (was '%s')" %
                         (exprTxt, str(val), str(real)))

    def testIf(self):
        """If expressions."""

        for exprTxt, val in (("if(1, 2, 3)", 2),
                             ("if(0, 2, 3)", 3),
                             ("if(true, 2, 3)", 2),
                             ("if(false, 2, 3)", 3),
                             ("if('a'='a', 'x', 'y')", 'x'),
                             ("if('a'='b', 'x', 'y')", 'y'),
                             ("if($a, 1, 2)", None),
                             ("if(true, 1=2, 1=1)", False),
                             ("if(false, 1=2, 1=1)", True),):
            expr = self.env.parseExpr(exprTxt)
            self.assert_(isinstance(expr, nodes.If))
            real = evaluate.reduceToValue(expr)
            self.assert_(real == val,
                         "Value for '%s' should be '%s' (was '%s')" %
                         (exprTxt, str(val), str(real)))


if __name__ == '__main__':
    unittest.main()
