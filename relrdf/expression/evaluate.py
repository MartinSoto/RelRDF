import operator

import nodes
import constnodes
import rewrite


class Evaluator(rewrite.ExpressionTransformer):
    """An expression transformer that reduces all constant
    subexpressions of an expression to simple constants."""

    def __init__(self):
        super(Evaluator, self).__init__(prePrefix='pre')

    def Equal(self, expr, *args):
        common = None
        for value in constnodes.constValues(args):
            if common is None:
                common = value
            elif unicode(common) != unicode(value):
                # Constant values aren't all equal.
                return nodes.Literal(False)

        if common is None:
            # No constant nodes.
            expr[:] = args
            return expr

        expr[:] = constnodes.nonConstExprs(args)

        if len(expr) > 0:
            expr[:0] = [nodes.Literal(common)]
            return expr
        else:
            # All subexpressions were constant nodes.
            return nodes.Literal(True)

    def Different(self, expr, op1, op2):
        common = None
        for value in constnodes.constValues(args):
            if common is None:
                common = value
            elif unicode(common) != unicode(value):
                # Constant values aren't all equal (i.e., there is a
                # pair of different values.)
                return nodes.Literal(True)

        if common is None:
            # No constant nodes.
            expr[:] = args
            return expr

        expr[:] = constnodes.nonConstExprs(args)

        if len(expr) > 0:
            expr[:0] = [nodes.Literal(common)]
            return expr
        else:
            # All subexpressions were constant nodes.
            return nodes.Literal(False)


    def _compOp(self, expr, operator, op1, op2):
        val1 = constnodes.constValue(op1)
        val2 = constnodes.constValue(op2)

        if val1 is None or val2 is None:
            expr[0] = op1
            expr[1] = op2
            return expr

        return nodes.Literal(operator(val1, val2))

    def LessThan(self, expr, op1, op2):
        return self._compOp(expr, operator.lt, op1, op2)

    def LessThanOrEqual(self, expr, op1, op2):
        return self._compOp(expr, operator.le, op1, op2)

    def GreaterThan(self, expr, op1, op2):
        return self._compOp(expr, operator.gt, op1, op2)

    def GreaterThanOrEqual(self, expr, op1, op2):
        return self._compOp(expr, operator.ge, op1, op2)


    def Or(self, expr, *args):
        if reduce(operator.__or__,
                  constnodes.constValues(args), False):
            return nodes.Literal(True)
        else:
            expr[:] = constnodes.nonConstExprs(args)
            if len(expr) > 0:
                return expr
            else:
                return nodes.Literal(False)

    def And(self, expr, *args):
        if reduce(operator.__and__,
                  constnodes.constValues(args), True):
            expr[:] = constnodes.nonConstExprs(args)
            if len(expr) > 0:
                return expr
            else:
                return nodes.Literal(True)
        else:
            return nodes.Literal(False)

    def Not(self, expr, op):
        val = constnodes.constValue(op)
        if val is not None:
            return nodes.Literal(not value)
        else:
            expr[0] = [op]
            return expr

    def preIf(self, expr):
        # Evaluate the condition first.
        cond = self.process(expr[0])
        condVal = constnodes.constValue(cond)

        if condVal is None:
            # The condition can't be reduced to a boolean value.
            return (cond, self.process(expr[1]), self.process(expr[2]))
        elif condVal:
            # Only evaluate the 'then' part.
            return (cond, self.process(expr[1]), expr[2])
        else:
            # Only evaluate the 'else' part.
            return (cond, expr[1], self.process(expr[2]))#

    def If(self, expr, cond, thenExpr, elseExpr):
        condVal = constnodes.constValue(cond)
        if condVal is None:
            expr[:] = (cond, thenExpr, elseExpr)
            return expr
        elif condVal:
            return thenExpr
        else:
            return elseExpr


_evaluator = Evaluator()

def reduceConst(expr):
    """Reduce constant subexpressions in `expr` to simple constants."""
    return _evaluator.process(expr)

def reduceToValue(expr):
    """Reduce a constant expression to a single Python value.

    Returns `None` if the expression can't be reduced."""
    reduced = _evaluator.process(expr)
    return constnodes.constValue(reduced)
