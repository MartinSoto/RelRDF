import re

from relrdf.commonns import xsd
from relrdf.expression import rewrite


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
        return ', '.join(operands)

    def Select(self, expr, rel, cond):
        return '%s\nWHERE %s' % (rel, cond)

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
        incarnation1 = 'table_%s' % expr[0].incarnation

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

    return emitter.process(expr)
