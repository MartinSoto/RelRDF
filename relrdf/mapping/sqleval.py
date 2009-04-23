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
