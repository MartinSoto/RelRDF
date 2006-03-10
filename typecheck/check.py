from error import TypeCheckError
from expression import nodes, rewrite

from typeexpr import rdfNodeType, LiteralType, genericLiteralType, \
     resourceType, RelationType


def error(expr, msg):
    raise TypeCheckError(extents=expr.getExtents(), msg=msg)


class TypeChecker(rewrite.ExpressionProcessor):
    """Perform type checking on an expression. Methods don't actually
    build any values but set them in the `staticType` and
    `dynamicType` fields of the expression."""

    __slots__ = ('scopeStack')

    def __init__(self):
        # A stack of RelationType objects for processing nested
        # Select and MapResult nodes.
        self.scopeStack = []

    def Uri(self, expr):
        expr.staticType = resourceType

    def Literal(self, expr):
        if expr.literal.typeUri is not None:
            expr.staticType = LiteralType(expr.literal.typeUri)
        else:
            expr.staticType = genericLiteralType

    def Var(self, expr):
        if len(self.scopeStack) > 0:
            typeExpr = self.scopeStack[-1].getColumnType(expr.name)
            if typeExpr is not None:
                expr.staticType = typeExpr
                expr.dynamicType = nodes.VarDynType(expr.name)

    def StatementPattern(self, expr, subjTp, predTp, objTp):
        typeExpr = RelationType()
        for i, subexpr in enumerate(expr):
            if i <= 1:
                if isinstance(subexpr, nodes.Var):
                    typeExpr.addColumn(subexpr.name, resourceType)
                elif subexpr.staticType != resourceType:
                    error(subexpr, _("Pattern %s can only be a resource") %
                          (i == 0 and "subject" or "predicate"))
            elif isinstance(subexpr, nodes.Var):
                typeExpr.addColumn(subexpr.name, rdfNodeType)
        expr.staticType = typeExpr

    def ReifStmtPattern(self, expr, varTp, subjTp, predTp, objTp):
        pass

    def Equal(self, expr, *operands):
        pass

    def LessThan(self, expr, operand1, operand2):
        pass

    def GreaterThan(self, expr, operand1, operand2):
        pass

    def GreaterThanOrEqual(self, expr, operand1, operand2):
        pass

    def Different(self, expr, *operands):
        pass

    def Or(self, expr, *operands):
        pass

    def And(self, expr, *operands):
        pass

    def Not(self, expr, operand):
        pass

    def Product(self, expr, *operands):
        typeExpr = RelationType()

        for subexpr in expr:
            subexprType = subexpr.staticType
            for columnName in subexprType.getColumnNames():
                if typeExpr.hasColumn(columnName):
                    columnType = typeExpr.getColumnType(columnName). \
                                 commonType(subexprType. \
                                            getColumnType(columnName))
                    if columnType is None:
                        error(expr, _("Incompatible types for variable '%s'")
                              % columnName)
                else:
                    columnType = subexprType.getColumnType(columnName)
                typeExpr.addColumn(columnName, columnType)

        expr.staticType = typeExpr

    def preSelect(self, expr):
        # Process the relation subexpression and create a scope from
        # its type.
        self.process(expr[0])
        self.scopeStack.append(expr[0].staticType)

        # Now process the condition.
        self.process(expr[1])

        # FIXME: Check for boolean type in the condition.

        # Remove the scope.
        self.scopeStack.pop()

        return (None,) * len(expr)

    def Select(self, expr, rel, predicate):
        expr.staticType = expr[0].staticType

    def preMapResult(self, expr):
        # Process the relation subexpression and create a scope from
        # its type.
        self.process(expr[0])
        self.scopeStack.append(expr[0].staticType)

        # Now process the mapping expressions.
        for mappingExpr in expr[1:]:
            self.process(mappingExpr)

        # Remove the scope.
        self.scopeStack.pop()

        return (None,) * len(expr)

    def MapResult(self, expr, rel, *mappingExprs):
        expr.staticType = expr[0].staticType

    def _setOperationType(self, expr, *operands):
        typeExpr = operands[0].staticType
        for subexpr in operands[1:]:
            typeExpr.generalizeType(subexpr.staticType)
            if typeExpr is None:
                error(expr, _("Incompatible types in set operation"))
        expr.staticType = typeExpr

    def Union(self, expr, *operands):
        self._setOperationType(expr, *operands)

    def SetDifference(self, expr, operand1, operand2):
        self._setOperationType(expr, *operands)

    def Intersection(self, expr, *operands):
        self._setOperationType(expr, *operands)

checker = TypeChecker()


def typeCheck(expr):
    """Type check `expr`. This function sets the `staticType` and
    `dynamicType` fields in all nodes in `expr`."""
    checker.process(expr, prePrefix="pre")
