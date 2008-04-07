import re

from relrdf.commonns import xsd, fn, sql
from relrdf.expression import rewrite, nodes, simplify, evaluate


class SqlEmitter(rewrite.ExpressionProcessor):
    """Generate SQL code from a relational expression."""

    __slots__ = ('distinct',)

    def __init__(self):
        super(SqlEmitter, self).__init__(prePrefix='pre')

        self.distinct = 0
        
    def Null(self, expr):
        return 'NULL'

    def Uri(self, expr):
        return "'%s'" % expr.uri

    _noStringTypes = set((xsd.boolean,
                          xsd.integer,
                          xsd.decimal,
                          xsd.double))

    def Literal(self, expr):
        if expr.literal.typeUri in self._noStringTypes:
            return "%s"  % unicode(expr.literal)
        else:
            return "'%s'" % unicode(expr.literal)

    _functionMap = {
        fn.abs:                'ABS',
        fn.ceiling:            'CEILING',
        fn.concat:             'CONCAT',
        fn['current-dateTime']:'NOW',
        fn.floor:              'FLOOR',
        fn['lower-case']:      'LOWER',
        fn.max:                'GREATEST',
        fn.min:                'LEAST',
        fn['not']:             'NOT',
        fn.round:              'ROUND',
        fn['upper-case']:      'UPPER'
    }
    
    def FunctionCall(self, expr, *params):
        # Find SQL function name. TODO: type checking, argument count
        fnName = self._functionMap.get(expr.functionName)
        if fnName == None:
            fnName = sql.getLocal(expr.functionName)
        if fnName == None:
            return '' # TODO: Throw something? Check in advance?
        return '%s(%s)' % (fnName, ', '.join(params))

    def If(self, expr, cond, thenExpr, elseExpr):
        return 'IF(%s, %s, %s)' % (cond, thenExpr, elseExpr)

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

    def Plus(self, expr, *operands):
        return '(' + ') + ('.join(operands) + ')'

    def Minus(self, expr, op1, op2):
        return '(%s) - (%s)' % (op1, op2)

    def UMinus(self, expr, op):
        return '-(%s)' % op

    def Times(self, expr, *operands):
        return '(' + ') * ('.join(operands) + ')'

    def DividedBy(self, expr, op1, op2):
        return '(%s) / (%s)' % (op1, op2)
    
    def IsBound(self, expr, var):
        return '%s IS NOT NULL' % var

    def CastBool(self, expr, var):
        return '(%s) != 0' % var

    def CastDecimal(self, expr, var):
        return 'CAST(%s AS DECIMAL)' % var

    def CastInt(self, expr, var):
        return 'CAST(%s AS SIGNED INTEGER)' % var

    def CastDateTime(self, expr, var):
        return 'CAST(%s AS DATETIME)' % var

    def CastString(self, expr, var):
        return 'CAST(%s AS CHAR)' % var
    
    def preMapValue(self, expr):
        if isinstance(expr[0], nodes.Select):
            # We treat this common case specially, in order to avoid
            # unnecessary nested queries.
            return ['%s WHERE %s' % (self.process(expr[0][0]),
                                      self.process(expr[0][1]))] + \
                   [self.process(subexpr) for subexpr in expr[1:]]
        else:
            return [self.process(subexpr) for subexpr in expr]
    
    def MapValue(self, expr, rel, sexpr):
        return '(SELECT %s FROM %s)' % (sexpr, rel);

    def Product(self, expr, *operands):
        # Note there is a special rule if parent node is Select (see preSelect)
        return '(' + ' CROSS JOIN '.join(operands) + ')'

    def preLeftJoin(self, expr):
        if isinstance(expr[1], nodes.Select):
            # We use this select's condition as join condition.
            return (self.process(expr[0]), self.process(expr[1][0]),
                     self.process(expr[1][1]))
        else:
            return (self.process(expr[0]), self.process(expr[1]),
                    None)

    def LeftJoin(self, expr, fixed, optional, cond):
        if cond is not None:
            return '(%s LEFT JOIN %s ON (%s))' % (fixed, optional, cond)
        else:
            # If no condition is available, this is actually a cross
            # join.
            return '(%s CROSS JOIN %s)' % (fixed, optional)

    def preSelect(self, expr):
        if isinstance(expr[0], nodes.Product):
            srel = [self.process(sub) for sub in expr[0]]
            return (' INNER JOIN '.join(srel), self.process(expr[1]))
        else:
            return (self.process(expr[0]), self.process(expr[1]))                        
        
    def Select(self, expr, rel, cond):
        if isinstance(expr[0], nodes.Product):
            # The relation is some sort of join, we can just add an
            # "ON" clause to it.
            return '(%s ON %s)' % (rel, cond)
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

        if len(expr.columnNames) > 0:
            columns = ', '.join(["%s AS %s" % (e, n)
                                 for e, n in zip(columnExprs, expr.columnNames)])
        else:
            columns = '*'

        # Distinct?
        if self.distinct:
            distinct = 'DISTINCT '
        else:
            distinct = ''

        if select == '':
            return 'SELECT %s%s' % (distinct, columns)
        else:
            return 'SELECT %s%s\nFROM %s' % (distinct, columns, select)

    def preDistinct(self, expr):
        self.distinct += 1
        return (self.process(expr[0]),)

    def Distinct(self, expr, subexpr):
        self.distinct -= 1
        return subexpr

    def OffsetLimit(self, expr, subexpr):
        
        # Check that we have some kind of SELECT expression in subexpr
        allowed = [nodes.MapResult, nodes.Select, nodes.Sort, nodes.Distinct]
        assert expr[0].__class__ in allowed,  \
            'OffsetLimit can only be used with the result of MapResult, Select, ' \
            'Distinct or Sort!'
        
        # Add LIMIT clause
        if expr.limit != None:
            if expr.offset != None:                
                query = subexpr + '\nLIMIT %d,%d' % (expr.offset, expr.limit)
            else:
                query = subexpr + '\nLIMIT %d' % expr.limit
        else:
            if expr.offset != None:
                # Note: The MySQL manual actually suggests this number.
                #       Let's hope it's future-proof.
                query = subepxr + '\nLIMIT %d,18446744073709551615' % expr.offset
            
        return query
    
    def Sort(self, expr, subexpr, orderBy):
        
        # Check that we have some kind of SELECT expression in subexpr
        allowed = [nodes.MapResult, nodes.Select, nodes.Sort, nodes.Distinct]
        assert expr[0].__class__ in allowed,  \
            'Sort can only be used directly with the result of MapResult, Distinct or Select!'
                    
        # Compose with order direction
        if expr.ascending:
            orderCrit = orderBy + " ASC"
        else:
            orderCrit = orderBy + " DESC"
        
        # Add (to) ORDER BY clause
        if isinstance(expr[0], nodes.Sort):
            query = subexpr + ", " + orderCrit
        else:
            query = subexpr + "\nORDER BY " + orderCrit
        
        return query

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

    def Empty(self, expr):
        return ''

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

    def SqlFunctionCall(self, expr, *args):
        return '%s(%s)' % (expr.name, ', '.join(args))


def emit(expr):
    emitter = SqlEmitter()

    # Simplify the expression first.
    expr = simplify.simplify(expr)

    # Reduce constant expressions.
    expr = evaluate.reduceConst(expr)

    return emitter.process(expr)

