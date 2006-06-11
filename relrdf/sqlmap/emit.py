import re

from relrdf.commonns import xsd
from relrdf.expression import rewrite, nodes, simplify


class SqlEmitter(rewrite.ExpressionProcessor):
    """Generate SQL code from a relational expression."""

    __slots__ = ('distinct',)

    def __init__(self):
        super(SqlEmitter, self).__init__(prePrefix='pre')

        self.distinct = False

    def Null(self, expr):
        return 'NULL'

    def Uri(self, expr):
        return '"%s"' % expr.uri

    def Literal(self, expr):
        if expr.literal.typeUri == xsd.decimal:
            return "%s"  % str(expr.literal)
        else:
            return '"%s"' % str(expr.literal)

    def FunctionCall(self, expr, *params):
        return '%s(%s)' % (expr.functionName, ', '.join(params))

    def Equal(self, expr, operand1, *operands):
        return ' AND '.join(['(%s) = (%s)' % (operand1, o) for o in operands])

    def LessThan(self, expr, operand1, operand2):
        return '(%s) < (%s)' % (operand1, operand2)

    def LessThanOrEqual(self, expr, operand1, operand2):
        return '(%s) <= (%s)' % (operand1, operand2)

    def GreaterThan(self, expr, operand1, operand2):
        return '(%s) > (%s)' % (operand1, operand2)

    def GreaterThanOrEqual(self, expr, operand1, operand2):
        return '(%s) >= (%s)' % (operand1, operand2)

    def Different(self, expr, *operands):
        disj = []
        for i, operand1 in enumerate(operands):
            for operand2 in operands[i + 1:]:
                disj.append('(%s) <> (%s)' % (operand1, operand2))
        return ' AND '.join(disj)

    def Or(self, expr, *operands):
        return '(' + ') OR ('.join(operands) + ')'

    def Not(self, expr, operand):
        return 'NOT (%s)' % operand

    def And(self, expr, *operands):
        return '(' + ') AND ('.join(operands) + ')'

    def Product(self, expr, *operands):
        return ' CROSS JOIN '.join(operands)

    def Select(self, expr, rel, cond):
        if isinstance(expr[0], nodes.Product):
            # The relation is some sort of join, we can just add an
            # "ON" clause to it.
            return '%s\nON %s' % (rel, cond)
        else:
            # If the expression is not a product it must have an
            # incarnation. We create a derived table which uses the
            # same incarnation as name.
            return '(SELECT * FROM %s WHERE %s) AS rel_%s' % \
                   (rel, cond, expr[0].incarnation)

    def preMapResult(self, expr):
        if isinstance(expr[0], nodes.Select):
            # We treat this common case specially, in order to avoid
            # unnecessary nested queries.
            return ['%s\nWHERE %s' % (self.process(expr[0][0]),
                                      self.process(expr[0][1]))] + \
                   [self.process(subexpr) for subexpr in expr[1:]]
        else:
            return [self.process(subexpr) for subexpr in expr]

    def MapResult(self, expr, select, *columnExprs):
        columns = ', '.join(["%s AS '%s'" % (e, n)
                             for e, n in zip(columnExprs, expr.columnNames)])
        if self.distinct:
            distinct = 'DISTINCT '
        else:
            distinct = ''
        return 'SELECT %s%s\nFROM %s' % (distinct, columns, select)

    def preDistinct(self, expr):
        self.distinct = True

        return (self.process(expr[0]),)

    def Distinct(self, expr, subexpr):
        return subexpr

    def Union(self, expr, *operands):
        return '(' + ')\nUNION\n('.join(operands) + ')'

    def _setDiffOrIntersect(self, compOperator, expr, operand1, operand2):
        incarnation1 = 'rel_%s' % expr[0].incarnation

        columns = ', '.join(['%s.%s AS %s' % (incarnation1, n, n)
                             for n in expr.columnNames])
        columnExprs = ', '.join(['%s.%s' % (incarnation1, n)
                                 for n in expr.columnNames])
        return 'SELECT %s\nFROM (%s) AS %s\nWHERE ROW(%s) %s (%s)' % \
               (columns, operand1, incarnation1, columnExprs, compOperator,
                operand2)

    def Intersection(self, *args):
        return self._setDiffOrIntersect('IN', *args)

    def SetDifference(self, *args):
        return self._setDiffOrIntersect('NOT IN', *args)

    def SqlRelation(self, expr):
        # Single relation names cannot be parenthesized.
        try:
            pos = expr.sqlCode.index(' ')
        except ValueError:
            pos = None

        if pos is not None:
            return '(%s) AS rel_%s' % (expr.sqlCode, expr.incarnation)
        else:
            return '%s AS rel_%s' % (expr.sqlCode, expr.incarnation)

    def SqlFieldRef(self, expr):
        return 'rel_%s.%s' % (expr.incarnation, expr.fieldId)

    _subexprPattern = re.compile(r'\$([0-9]+)\$')

    def SqlScalarExpr(self, expr, *subexprs):
        def repl(match):
            return subexprs[int(match.group(1))]

        return self._subexprPattern.sub(repl, expr.sqlExpr)


def emit(expr):
    emitter = SqlEmitter()

    # Simplify the expression first.
    expr = simplify.simplify(expr)

    return emitter.process(expr)
