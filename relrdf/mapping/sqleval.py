from relrdf.expression import evaluate, constnodes

import sqlfunctions


class SqlEvaluator(evaluate.Evaluator):
    """An expression transformer that reduces all constant
    subexpressions of an expression to simple constants. This class
    also includes support for the special SQL-specific expression
    nodes."""

    def SqlFunctionCall(self, expr, *args):
        try:
            return sqlfunctions.evalFunction(expr.name, *args)
        except sqlfunctions.StaticEvalError:
            # Static evaluation is not possible.
            expr[:] = args
            return expr


_evaluator = SqlEvaluator()

def reduceConst(expr):
    """Reduce all constant subexpressions in `expr` to simple
    constants."""
    return _evaluator.process(expr)

def reduceToValue(expr):
    """Reduce a constant expression to a single Python value.

    Returns `None` if the expression can't be reduced."""
    reduced = _evaluator.process(expr)
    return constnodes.constValue(reduced)
