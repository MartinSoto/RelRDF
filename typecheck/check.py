from commonns import xsd

from error import TypeCheckError
from expression import nodes, rewrite

from typeexpr import rdfNodeType, LiteralType, booleanLiteralType, \
     genericLiteralType, ResourceType, resourceType, RelationType


def error(expr, msg):
    raise TypeCheckError(extents=expr.getExtents(), msg=msg)


class TypeChecker(rewrite.ExpressionProcessor):
    """Perform type checking on an expression. Methods don't actually
    build any values but set them in the `staticType` and
    `dynamicType` fields of the expression."""

    __slots__ = ('scopeStack')

    def __init__(self):
        super(TypeChecker, self).__init__(prePrefix="pre")

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

    def _checkPattern(self, expr, subexprs):
        typeExpr = RelationType()
        for i, subexpr in enumerate(subexprs):
            if i <= 1:
                if isinstance(subexpr, nodes.Var):
                    typeExpr.addColumn(subexpr.name, resourceType)
                elif subexpr.staticType != resourceType:
                    error(subexpr, _("Pattern %s can only be a resource") %
                          (i == 0 and "subject" or "predicate"))
            elif isinstance(subexpr, nodes.Var):
                typeExpr.addColumn(subexpr.name, rdfNodeType)
        expr.staticType = typeExpr

    def StatementPattern(self, expr, subjTp, predTp, objTp):
        self._checkPattern(expr, expr)

    def ReifStmtPattern(self, expr, varTp, subjTp, predTp, objTp):
        self._checkPattern(expr, expr[1:])
        expr.staticType.addColumn(expr[0].name, resourceType)

    def _checkScalarOperands(self, expr, opName):
        for i, subexpr in enumerate(expr):
            if isinstance(subexpr.staticType, RelationType):
                error(expr,
                      _("Operand %d to '%s' must be scalar") % \
                      (i + 1, opName))

    def Equal(self, expr, *operands):
        self._checkScalarOperands(expr, '=')
        expr.staticType = booleanLiteralType

    def Different(self, expr, *operands):
        self._checkScalarOperands(expr, '!=')
        expr.staticType = booleanLiteralType

    def _checkNoResourceOperands(self, expr, opName):
        for i, subexpr in enumerate(expr):
            if isinstance(subexpr.staticType, ResourceType):
                error(expr,
                      _("Operand %d to '%s' is not allowed to be a resource") % \
                      (i + 1, opName))

    def LessThan(self, expr, operand1, operand2):
        self._checkScalarOperands(expr, '<')
        self._checkNoResourceOperands(expr, '<')
        expr.staticType = booleanLiteralType

    def LessThanOrEqual(self, expr, operand1, operand2):
        self._checkScalarOperands(expr, '<=')
        self._checkNoResourceOperands(expr, '<=')
        expr.staticType = booleanLiteralType

    def GreaterThan(self, expr, operand1, operand2):
        self._checkScalarOperands(expr, '>')
        self._checkNoResourceOperands(expr, '>')
        expr.staticType = booleanLiteralType

    def GreaterThanOrEqual(self, expr, operand1, operand2):
        self._checkScalarOperands(expr, '>=')
        self._checkNoResourceOperands(expr, '>=')
        expr.staticType = booleanLiteralType

    def Or(self, expr, *operands):
        self._checkScalarOperands(expr, 'OR')
        expr.staticType = booleanLiteralType

    def And(self, expr, *operands):
        self._checkScalarOperands(expr, 'AND')
        expr.staticType = booleanLiteralType

    def Not(self, expr, operand):
        self._checkScalarOperands(expr, 'NOT')
        expr.staticType = booleanLiteralType

    def Product(self, expr, *operands):
        typeExpr = RelationType()

        for subexpr in expr:
            subexprType = subexpr.staticType
            for columnName in subexprType.getColumnNames():
                if typeExpr.hasColumn(columnName):
                    columnType = typeExpr.getColumnType(columnName). \
                                 intersectType(subexprType. \
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

        # Remove the scope.
        self.scopeStack.pop()

        return (None,) * len(expr)

    def Select(self, expr, rel, predicate):
        if not isinstance(expr[1].staticType, LiteralType) or \
           expr[1].staticType.typeUri != xsd.boolean:
            error(expr, _("Condition must be boolean"))
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
        typeExpr = RelationType()
        for colName, colExpr in zip(expr.columnNames, expr[1:]):
            typeExpr.addColumn(colName, colExpr.staticType)
        expr.staticType = typeExpr

    def _setOperationType(self, expr, *operands):
        typeExpr = expr[0].staticType
        for subexpr in expr[1:]:
            typeExpr.generalizeType(subexpr.staticType)
            if typeExpr is None:
                error(expr, _("Incompatible types in set operation"))
        expr.staticType = typeExpr

    def Union(self, expr, *operands):
        self._setOperationType(expr, *operands)

    def SetDifference(self, expr, operand1, operand2):
        self._setOperationType(expr, operand1, operand2)

    def Intersection(self, expr, *operands):
        self._setOperationType(expr, *operands)


def typeCheck(expr):
    """Type check `expr`. This function sets the `staticType` and
    `dynamicType` fields in all nodes in `expr`. `expr` will be
    modified in place, but the return value must be used since the
    root node may change."""
    checker = TypeChecker()
    checker.process(expr)
    return expr

