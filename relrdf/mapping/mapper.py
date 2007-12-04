import operator

from relrdf import error
from relrdf.expression import nodes, evaluate

import valueref
import transform

class MacroMapper(transform.StandardReifTransformer):
    """A mapper based on macro expressions."""

    __slots__ = ('matchClauses',
                 'defCls')

    def __init__(self):
        super(MacroMapper, self).__init__()

        self.matchClauses = []
        self.defCls = None

    def addMatch(self, argPos, exprCls, condCls=None):
        self.matchClauses.append((argPos, exprCls, condCls))

    def setDefault(self, expr):
        self.defCls = expr

    def replStatementPattern(self, expr):
        # First try the match clauses in order.
        for argPos, exprCls, condCls in self.matchClauses:
            # Retrieve the relevant macro arguments from the original
            # query pattern.
            clauseArgs = [expr[i] for i in argPos]

            # If the macro arguments contain variables, this match
            # clause is not applicable.
            if reduce(operator.__or__,
                      (isinstance(e, nodes.Var) for e in clauseArgs)):
                continue

            # If there's a condition, verify it.
            if condCls is not None:
               val = evaluate.reduceToValue(condCls.expand(*clauseArgs))
               if val is None:
                   raise error.SchemaError(msg=('Condition must be a '
                                                'constant expression'),
                                           extents=condCls.getExtents())
               if not val:
                   continue

            # This match clause has been selected. Expand the
            # expression and return it.
            replExpr = exprCls.expand(*clauseArgs)
            return (replExpr,
                    ('context', 'subject', 'predicate', 'object'))

        # No match clause was selected. Expand and return the default
        # expression.
        replExpr = self.defCls
        return (replExpr,
                ('context', 'subject', 'predicate', 'object'))
