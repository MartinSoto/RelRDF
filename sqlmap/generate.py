from commonns import xsd
from expression import rewrite


class SqlGenerator(rewrite.ExpressionProcessor):
    __slots__ = ()

    def Uri(self, expr):
        return '"%s"' % expr.uri

    def Literal(self, expr):
        if expr.literal.typeUri == xsd.decimal:
            return "%s"  % str(expr.literal)
        else:
            return '"%s"' % str(expr.literal)

    def FieldRef(self, expr):
        return '%s_%s.%s' % (expr.relName, expr.incarnation, expr.fieldId)

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

    def Relation(self, expr):
        return '%s AS %s_%s' % (expr.name, expr.name, expr.incarnation)

    def Product(self, expr, *operands):
        return ', '.join(operands)

    def Select(self, expr, rel, cond):
        return 'FROM %s\nWHERE %s' % (rel, cond)

    def MapResult(self, expr, select, *columnExprs):
        columns = ', '.join(['%s AS %s' % (e, n)
                             for e, n in zip(columnExprs, expr.columnNames)])
        return 'SELECT %s\n%s' % (columns, select)

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

generator = SqlGenerator()


def generate(expr):
    return generator.process(expr)
