import operator

from relrdf import error
from relrdf.expression import nodes, evaluate

import valueref
import transform


class BasicMapper(transform.PureRelationalTransformer):
    """A base mapper for the MySQL basic schema. It handles the
    mapping of type expressions."""

    def prepareConnection(self, connection):
        """Prepares the database connection (e.g., by creating certain
        temporary tables) for use with this mapping."""
        pass

    def releaseConnection(self, connection):
        """Releases any resources created by the `prepareConnection`
        method."""
        pass

    def mapTypeExpr(self, typeExpr):
        if isinstance(typeExpr, LiteralType):
            # FIXME:Search for the actual type id.
            return nodes.Literal(TYPE_ID_LITERAL)
        elif isinstance(typeExpr, BlankNodeType):
            return nodes.Literal(TYPE_ID_BLANKNODE)
        elif isinstance(typeExpr, ResourceType):
            return nodes.Literal(TYPE_ID_RESOURCE)
        else:
            assert False, "Cannot determine type"


class MacroMapper(BasicMapper,
                  transform.StandardReifTransformer):
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
            return exprCls.expand(*clauseArgs)

        # No match clause was selected. Expand a return the default
        # expression.
        return self.defCls
