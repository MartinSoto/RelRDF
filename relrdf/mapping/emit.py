# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2009 Fraunhofer-Institut fuer Experimentelles
#                         Software Engineering (IESE).
#
# RelRDF is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.


import sys
import re

from relrdf.commonns import xsd, fn, sql, rdfs
from relrdf.expression import uri, rewrite, nodes

import string

# Adapted from pgdb.
def quote(str):
    str = unicode(str)
    str = str.replace('\\', '\\\\')
    str = str.replace("'", "''")
    return "E'"+ str + "'"

def listJoinIter(*args):
    """Produces a sequence conformed by the elements of `args[-1]`
    (i.e., the last parameter must be a sequence) with all other
    parameters (i.e., the elements of `args[:-1]`) placed as a
    separator between each pair of elements from `args[-1]`."""
    sep, list = args[:-1], args[-1]

    if len(list) == 0:
        return

    yield list[0]
    for elem in list[1:]:
        for sepElem in sep:
            yield sepElem
        yield elem

def listJoin(*args):
    """`listJoinIter` as a tuple."""
    return tuple(listJoinIter(*args))
    

class SqlEmitter(rewrite.ExpressionProcessor):
    """Generate SQL code from a relational expression.

    The result of running this processor on an expression is either a
    string or an iterable object. If it is an iterable object, it must
    contain strings or other iterable objects built the same way. The
    actual SQL expression can be obtained by flattening this structure
    (i.e., traversing it depth-first) and concatenating the resulting
    strings. The nesting structure should reflect the syntactical
    structure of the resulting SQL, and can be used for pretty
    printing."""

    __slots__ = ('distinct',
                 'sort',
                 'offsetLimit',)

    def __init__(self):
        super(SqlEmitter, self).__init__(prePrefix='pre')

        self.distinct = None
        self.sort = None
        self.offsetLimit = None

    def _lookupTypeId(self, uri, tag):
        if uri is not None:
            return ('(', 'SELECT ', 'id', ' FROM ', 'types', ' WHERE ',
                    'type_uri', '=', quote(uri), ')')
        elif tag is not None:
            return ('(', 'SELECT ', 'id', ' FROM ', 'types', ' WHERE ',
                    'lang_tag', '=', quote(tag), ')')
        else:
            return '1'

    def Null(self, expr):
        return 'NULL'

    def SqlInt(self, expr):
        return str(expr.val)

    def Uri(self, expr):
        return 'rdf_term_resource(%s)' % quote(expr.uri)

    def Literal(self, expr):
        # Type ID lookup.
        typeIdExpr = self._lookupTypeId(expr.literal.typeUri,
                                        expr.literal.lang)

        return ('rdf_term(', typeIdExpr, ', ', quote(expr.literal), ')')

    def If(self, expr, cond, thenExpr, elseExpr):
        return ('IF', '(', cond, ', ', thenExpr, ', ', elseExpr, ')')

    def SqlCastBool(self, expr, subexpr):
        return ('!!', '(', subexpr, ')')

    def SqlEqual(self, expr, operand1, *operands):
        return listJoin(' AND ', [('(', operand1, ')', ' = ', '(', o, ')')
                                  for o in operands])

    def SqlIn(self, expr, operand1, operand2):
        return ('(', operand1, ')', ' IN ', '(', operand2, ')')

    def SqlLessThan(self, expr, operand1, operand2):
        return ('(', operand1, ')', ' < ', '(', operand2, ')')

    def SqlLessThanOrEqual(self, expr, operand1, operand2):
        return ('(', operand1, ')', ' <= ', '(', operand2, ')' , )

    def SqlGreaterThan(self, expr, operand1, operand2):
        return ('(', operand1, ')', ' > ', '(', operand2, ')')

    def SqlGreaterThanOrEqual(self, expr, operand1, operand2):
        return ('(', operand1, ')', ' >= ', '(', operand2, ')')

    def SqlDifferent(self, expr, *operands):
        disj = []
        for i, operand1 in enumerate(operands):
            for operand2 in operands[i + 1:]:
                disj.append(('(', operand1, ')', ' <> ', '(', operand2, ')'))
        return listJoin(' AND ', disj)

    def SqlTypeCompatible(self, expr, operand1, *operands):
        return listJoin(' AND ', [('(', operand1, ')', ' === ', '(', o, ')')
                                  for o in operands])

    def SqlOr(self, expr, *operands):
        return ('(',) + listJoin(')', ' OR ', '(', operands) + (')',)

    def SqlNot(self, expr, operand):
        return ('NOT ', '(', operand, ')')

    def SqlAnd(self, expr, *operands):
        return ('(',) + listJoin(')', ' AND ', '(', operands) + (')',)

    def Plus(self, expr, *operands):
        return ('(',) + listJoin(') + ', '(', operands) + (')',)

    def UPlus(self, expr, op):
        return ('+', '(', op, ')')

    def Minus(self, expr, op1, op2):
        return ('(', op1, ')', ' - ', '(', op2, ')')

    def UMinus(self, expr, op):
        return ('-', '(', op, ')')

    def Times(self, expr, *operands):
        return ('(',) + listJoin(')', ' * ', '(', operands) + (')',)

    def DividedBy(self, expr, op1, op2):
        return ('(', op1, ')', ' / ', '(', op2, ')')

    def IsBound(self, expr, var):
        return 'rdf_term_bound(%s)' % var

    def IsURI(self, expr, sexpr):
        return 'rdf_term_is_uri(%s)' % sexpr

    def IsBlank(self, expr, sexpr):
        return 'rdf_term_is_bnode(%s)' % sexpr

    def IsLiteral(self, expr, sexpr):
        return 'rdf_term_is_literal(%s)' % sexpr

    def Cast(self, expr, sexpr):
        return ('rdf_term_cast(', self._lookupTypeId(expr.type, None),
                ', ', sexpr, ')')

    def preMapValue(self, expr):
        if isinstance(expr[0], nodes.Select):
            # We treat this common case especially, in order to avoid
            # unnecessarily nested queries.
            return [(self.process(expr[0][0]), ' WHERE ',
                     self.process(expr[0][1]))] + \
                   [self.process(subexpr) for subexpr in expr[1:]]
        else:
            return [self.process(subexpr) for subexpr in expr]

    def MapValue(self, expr, rel, sexpr):
        return ('(', 'SELECT ', sexpr, ' FROM ', rel, ')');

    def Product(self, expr, *operands):
        # Note there is a special rule if parent node is Select (see
        # preSelect).
        return ('(',) + listJoin(' CROSS JOIN ', operands) + (')',)

    def LeftJoin(self, expr, fixed, optional, cond=None):
        if cond is not None:
            return ('(', fixed, ' LEFT JOIN ', optional, ' ON (',
                    cond, ')', ')')
        else:
            return ('(', fixed, ' LEFT JOIN ', optional, ' ON TRUE', ')')

    def preSelect(self, expr):
        if isinstance(expr[0], nodes.Product):
            assert len(expr[0]) > 1
            srel = [self.process(sub) for sub in expr[0]]
            # We need cross joins here except for the last one, which
            # must be an inner join so that we can attach the
            # condition to it. Joins associate left to right, so this
            # is guaranteed to work without parentheses.
            return (listJoin(' CROSS JOIN ', srel[:-1]) +
                    (' INNER JOIN ', srel[-1]),
                    self.process(expr[1]))
        else:
            return (self.process(expr[0]), self.process(expr[1]))

    def Select(self, expr, rel, cond):
        if isinstance(expr[0], nodes.Product):
            # The relation is some sort of join, we can just add an
            # "ON" clause to it.
            return ('(', rel, ' ON ', cond, ')')
        else:
            # If the expression is not a product it must have an
            # incarnation. We create a derived table which uses the
            # same incarnation as name.
            return ('(', 'SELECT * FROM ', rel, ' WHERE ', cond, ')', ' AS ',
                    'rel_%s' % expr[0].incarnation)

    def preMapResult(self, expr):
        # If any of the result modifier fields was already changed
        # something really evil is going on, such as a nested
        # MapResult.
        assert self.distinct is None
        assert self.sort is None
        assert self.offsetLimit is None

        # Process any result modifiers present in the expression.
        subexpr = expr[0]
        while isinstance(subexpr, nodes.QueryResultModifier):
            if isinstance(subexpr, nodes.Distinct):
                self.distinct = True

            elif isinstance(subexpr, nodes.Sort):
                orderBy = self.process(subexpr[1])
                if subexpr.ascending:
                    orderCrit = (orderBy, ' ASC')
                else:
                    orderCrit = (orderBy, ' DESC')

                # Accumulate sort nodes.
                if self.sort is None:
                    self.sort = (orderCrit,)
                else:
                    self.sort = (orderCrit, ', ') + self.sort

            elif isinstance(subexpr, nodes.OffsetLimit):
                if subexpr.limit is not None:
                    if subexpr.offset is not None:
                        self.offsetLimit = (' LIMIT ', str(subexpr.limit),
                                            ' OFFSET ', str(subexpr.offset))
                    else:
                        self.offsetLimit = (' LIMIT ', str(subexpr.limit))
                elif subexpr.offset != None:
                    self.offsetLimit = (' OFFSET ', str(subexpr.offset))

            subexpr = subexpr[0]

        # Process the body.
        if isinstance(subexpr, nodes.Select):
            # We treat this common case specially, in order to avoid
            # unnecessary nested queries.
            return [(self.process(subexpr[0]), ' WHERE ',
                     self.process(subexpr[1]))] + \
                   [self.process(mappingExpr) for mappingExpr in expr[1:]]
        else:
            return [self.process(subexpr)] + \
                   [self.process(mappingExpr) for mappingExpr in expr[1:]]

    def MapResult(self, expr, select, *columnExprs):
        if len(expr.columnNames) > 0:
            columns = listJoin(', ',
                               [(e, ' AS ', n)
                                for e, n in zip(columnExprs,
                                                expr.columnNames)])
        else:
            columns = '*'

        if self.distinct:
            distinct = 'DISTINCT '
        else:
            distinct = ''

        query = ('SELECT ', distinct, columns, ' FROM ') + select

        if self.sort:
            query += (' ORDER BY ',) + self.sort + (' NULLS FIRST',)

        if self.offsetLimit:
            query += self.offsetLimit

        return query

    def Union(self, expr, *operands):
        return ('(',) + listJoin(')', ' UNION ALL ', '(', operands) + (')',)

    def _setDiffOrIntersect(self, compOperator, expr, operand1, operand2):
        incarnation1 = 'rel_%s' % expr[0].incarnation

        columns = listJoin(', ', [(incarnation1, '.', n, ' AS ', n)
                                  for n in expr.columnNames])
        columnExprs = listJoin(', ', [(incarnation1, '.', n)
                                      for n in expr.columnNames])
        return ('SELECT ', columns, ' FROM ', '(', operand1, ')', ' AS ',
                incarnation1, ' WHERE ROW', '(', columnExprs, ')', ' ',
                compOperator, ' ', '(', operand2, ')')

    def Intersection(self, *args):
        return self._setDiffOrIntersect('IN', *args)

    def SetDifference(self, *args):
        return self._setDiffOrIntersect('NOT IN', *args)

    def Empty(self, expr):
        return ('(VALUES (1))', ' AS ', 'empty_rel(x)', ' WHERE ',
                'empty_rel.x = 0')

    def Project(self, expr, rel, *mappingExprs):
         columns = listJoin(', ',
                            [(e, ' AS ', n)
                             for e, n in zip(mappingExprs,
                                             expr.columnNames)])

         return ('SELECT ', columns, ' FROM ', rel)

    def SqlRelation(self, expr):
        # Single relation names cannot be parenthesized.
        try:
            pos = expr.sqlCode.index(' ')
        except ValueError:
            pos = None

        if pos is not None:
            return ('(', expr.sqlCode, ')', ' AS rel_%s' % expr.incarnation)
        else:
            return (expr.sqlCode, ' AS rel_%s' % expr.incarnation)

    def SqlFieldRef(self, expr):
        return 'rel_%s.%s' % (expr.incarnation, expr.fieldId)

    def SqlTypedFieldRef(self, expr):
        return 'rel_%s.%s' % (expr.incarnation, expr.fieldId)

    def SqlAs(self, expr, subexpr):
        return ('(', subexpr, ')', ' AS  rel_%s' % expr.incarnation)

    _subexprPattern = re.compile(r'\$([0-9]+)\$')

    def SqlScalarExpr(self, expr, *subexprs):
        def repl(match):
            return subexprs[int(match.group(1))]

        return self._subexprPattern.sub(repl, expr.sqlExpr)

    def SqlFunctionCall(self, expr, *args):
        return (expr.name, '(', listJoin(', ', args), ')')

    def SqlInArray(self, expr, val, array):
        return ('intset', '(', val, ')', ' <@ ', '(', array, ')')

    def BlankNode(self, expr):
        # Generate a unique UUID for the name used to identify the
        # blank node. Note this will produce the same blank node in
        # all result rows, so the blank nodes will have to be
        # reinstantiated afterwards.
        blank = uri.newBlankFromName(expr.name)
        return "rdf_term_resource('%s#reinst')" % unicode(blank)

    def LangMatches(self, expr, sexpr1, sexpr2):
        return ('rdf_term_lang_matches(', sexpr1, ', ', sexpr2, ')')


def traverseEmitted(seqOrStr):
    """Iterate over the sequence of strings in the results of the
    emitter, in depth-first order."""
    if isinstance(seqOrStr, basestring):
        yield seqOrStr
        return
    else:
        for elem in seqOrStr:
            for s in traverseEmitted(elem):
                yield s

def emittedText(seqOrStr):
    return ''.join(traverseEmitted(seqOrStr)).strip()

def prettyPrintStream(seqOrStr, stream=None, indent=0, width=78,
                      breakMin=20):
    """Pretty print a SQL expression into an output stream.

    The SQL expression is stored as a potentially nested sequence of
    strings as produced by the emitter.
    """
    if stream is None:
        stream = sys.stdout

    def recurse(seqOrStr, indent):
        if isinstance(seqOrStr, basestring):
            # We have a string, it's not possible to break it into
            # lines anyway.
            stripped = seqOrStr.strip()
            if len(stripped) > 0:
                stream.write(' ' * indent)
                stream.write(stripped)
                stream.write('\n')
            return

        oneLine = emittedText(seqOrStr)
        if len(oneLine) <= breakMin or indent + len(oneLine) <= width:
            if len(oneLine) > 0:
                # The whole expression fits into the allotted width.
                stream.write(' ' * indent)
                stream.write(oneLine)
                stream.write('\n')
            return

        # Print direct string subexpressions at this indent level and
        # sequence subexpressions at the next indent level.
        for subexpr in seqOrStr:
            if isinstance(subexpr, basestring):
                recurse(subexpr, indent)
            else:
                recurse(subexpr, indent + 2)

    recurse(seqOrStr, indent)

def prettyPrint(seqOrStr, indent=0, width=78, breakMin=20):
    """Pretty print a SQL expression and return the result as a
    string.

    The SQL expression is stored as a potentially nested sequence of
    strings as produced by the emitter.
    """
    import StringIO

    stream = StringIO.StringIO()
    prettyPrintStream(seqOrStr, stream, indent, width, breakMin)
    result = stream.getvalue()
    stream.close()
    return result

def emit(expr):
    emitter = SqlEmitter()
    #return prettyPrint(emitter.process(expr))
    return emittedText(emitter.process(expr))

