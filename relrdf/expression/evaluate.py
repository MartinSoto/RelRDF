import operator

import nodes
import rewrite


def isConstNode(expr):
    return isinstance(expr, nodes.Uri) or \
           isinstance(expr, nodes.Literal)

def constValue(expr):
    if isinstance(expr, nodes.Uri):
        return expr.uri
    elif isinstance(expr, nodes.Literal):
        return expr.literal.value
    return None

def constValues(exprs):
    for expr in exprs:
        if isinstance(expr, nodes.Uri):
            yield expr.uri
        elif isinstance(expr, nodes.Literal):
            yield expr.literal.value

def nonConstExprs(exprs):
    for expr in exprs:
        if not isConstNode(expr):
            yield expr


class Evaluator(rewrite.ExpressionTransformer):
    """An expression transformer that reduces all constant
    subexpressions of an expression to simple constants."""

    def Equal(self, expr, *args):
        common = None
        for value in constValues(args):
            if common is None:
                common = value
            elif unicode(common) != unicode(value):
                # Constant values aren't all equal.
                return nodes.Literal(False)

        if common is None:
            # No constant nodes.
            expr[:] = args
            return expr

        expr[:] = nonConstExprs(args)

        if len(expr) > 0:
            expr[:0] = [nodes.Literal(common)]
            return expr
        else:
            # All subexpressions were constant nodes.
            return nodes.Literal(True)

    def Different(self, expr, op1, op2):
        common = None
        for value in constValues(args):
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

        expr[:] = nonConstExprs(args)

        if len(expr) > 0:
            expr[:0] = [nodes.Literal(common)]
            return expr
        else:
            # All subexpressions were constant nodes.
            return nodes.Literal(False)


    def _compOp(self, expr, operator, op1, op2):
        val1 = constValue(op1)
        val2 = constValue(op2)

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
        if reduce(operator.__or__, constValues(args), False):
            return nodes.Literal(True)
        else:
            expr[:] = nonConstExprs(args)
            if len(expr) > 0:
                return expr
            else:
                return nodes.Literal(False)

    def And(self, expr, *args):
        if reduce(operator.__and__, constValues(args), True):
            expr[:] = nonConstExprs(args)
            if len(expr) > 0:
                return expr
            else:
                return nodes.Literal(True)
        else:
            return nodes.Literal(False)

    def Not(self, expr, op):
        val = constValue(op)
        if val is not None:
            return nodes.Literal(not value)
        else:
            expr[0] = [op]
            return expr


_evaluator = Evaluator()

def reduceConst(expr):
    """Reduce constant subexpressions in `expr` to simple constants."""
    return _evaluator.process(expr)
