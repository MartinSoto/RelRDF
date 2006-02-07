from expression import rewrite


class SqlGenerator(object):
    __slots__ = ()

    def Uri(self, expr):
        return '"%s"' % expr.uri

    def Literal(self, expr):
        return str(expr.literal)

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
        return '%s %s_%s' % (expr.name, expr.name, expr.incarnation)

    def Product(self, expr, *operands):
        return ', '.join(operands)

    def Select(self, expr, rel, cond):
        return 'FROM %s\nWHERE %s' % (rel, cond)

    def MapResult(self, expr, select, *columnExprs):
        columns = ', '.join(['%s %s' % (e, n)
                             for e, n in zip(columnExprs, expr.columnNames)])
        return 'SELECT %s\n%s' % (columns, select)


def generate(expr):
    generator = SqlGenerator()
    return rewrite.mapObject(generator, expr)
