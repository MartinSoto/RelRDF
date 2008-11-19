from relrdf.localization import _
from relrdf.commonns import xsd

from relrdf.expression import nodes, rewrite

from typeexpr import typeType, nullType, rdfNodeType, LiteralType, \
     booleanLiteralType, genericLiteralType, ResourceType, \
     resourceType, RelationType, StatementRelType

from typeexpr import error


class TypeChecker(rewrite.ExpressionProcessor):
    """Perform type checking on an expression. Methods don't actually
    build any values but set them in the ``staticType`` and
    ``failSafe`` fields of the expression."""

    __slots__ = ('scopeStack',)

    def __init__(self):
        super(TypeChecker, self).__init__(prePrefix="pre")

        # A stack of RelationType objects for processing nested
        # Select and MapResult nodes.
        self.scopeStack = []

    def createScope(self, relType):
        """Create a new variable scope on top of the stack,
        corresponding to the relation type `relType`."""
        self.scopeStack.append(relType)

    def closeScope(self):
        """Close (destroy) the topmost scope in the stack and return
        its associated relation type."""
        return self.scopeStack.pop()

    def lookUpVar(self, varName, nested=False):
        """Search for a variable named `varName` in the scope stack
        and return its type, or `nullType` if not found. If `nested`
        is `False` the variable will be searched for only in the
        topmost scope. Otherwise, the search will continue down the
        stack until one scope is found containing the variable or the
        bottom is reached."""
        if len(self.scopeStack) == 0:
            return nullType

        typeExpr = self.scopeStack[-1].getColumnType(varName)

        if nested and typeExpr == nullType:
            for scope in reversed(self.scopeStack[:-1]):
                typeExpr = scope.getColumnType(varName)
                if typeExpr != nullType:
                    return typeExpr

        return typeExpr


    def Uri(self, expr):
        expr.staticType = resourceType
        expr.failSafe = True

    def Literal(self, expr):
        if expr.literal.typeUri is not None:
            expr.staticType = LiteralType(expr.literal.typeUri)
        else:
            expr.staticType = genericLiteralType
        expr.failSafe = True
            
    def FunctionCall(self, expr, *params):
        self._checkScalarOperands(expr, expr.functionName)
        expr.staticType = genericLiteralType

    def Var(self, expr):
        expr.staticType = self.lookUpVar(expr.name)

    def BlankNode(self, expr):
        expr.staticType = resourceType

    def _checkPattern(self, expr, subexprs):
        typeExpr = RelationType()
        for i, subexpr in enumerate(subexprs):
            if 1 <= i <= 2:
                if isinstance(subexpr, nodes.Var):
                    typeExpr.addColumn(subexpr.name, resourceType)

                    # Give this variable a type.
                    subexpr.staticType = resourceType
                elif subexpr.staticType != resourceType:
                    error(subexpr, _("Pattern %s can only be a resource") %
                          ('context', 'subject', 'predicate')[i])
            elif isinstance(subexpr, nodes.Var):
                typeExpr.addColumn(subexpr.name, rdfNodeType)

                # Give this variable a type.
                subexpr.staticType = rdfNodeType
        expr.staticType = typeExpr

    def StatementPattern(self, expr, ctxTp, subjTp, predTp, objTp):
        self._checkPattern(expr, expr)

    def ReifStmtPattern(self, expr, ctxTp, stmtTp, subjTp, predTp, objTp):
        self._checkPattern(expr, expr[0:1] + expr[2:])
        expr.staticType.addColumn(expr[1].name, resourceType)

    def DefaultGraph(self, expr):
        expr.staticType = resourceType
        expr.failSafe = True

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

    def Plus(self, expr, *operands):
        self._checkScalarOperands(expr, '+')
        expr.staticType = genericLiteralType

    def UPlus(self, expr, *operands):
        self._checkScalarOperands(expr, '+')
        expr.staticType = genericLiteralType
        
    def Minus(self, expr, *operands):
        self._checkScalarOperands(expr, '-')
        expr.staticType = genericLiteralType

    def UMinus(self, expr, *operands):
        self._checkScalarOperands(expr, '-')
        expr.staticType = genericLiteralType

    def Times(self, expr, *operands):
        self._checkScalarOperands(expr, '*')
        expr.staticType = genericLiteralType

    def DividedBy(self, expr, *operands):
        self._checkScalarOperands(expr, '/')
        expr.staticType = genericLiteralType
        
    def IsBound(self, expr, var):
        self._checkScalarOperands(expr, 'BOUND')
        expr.staticType = booleanLiteralType

    def IsURI(self, expr, var):
        self._checkScalarOperands(expr, 'IS_URI')
        expr.staticType = booleanLiteralType

    def IsBlank(self, expr, var):
        self._checkScalarOperands(expr, 'IS_BLANK')
        expr.staticType = booleanLiteralType

    def IsLiteral(self, expr, var):
        self._checkScalarOperands(expr, 'IS_LITERAL')
        expr.staticType = booleanLiteralType

    def Cast(self, expr, sexpr):
        self._checkScalarOperands(expr, 'CAST')
        expr.staticType = LiteralType(expr.type)
        
    def MapValue(self, expr, rel, sexpr):
        expr.staticType = expr[1].staticType
  
    def _checkJoin(self, expr, *operands):
        typeExpr = RelationType()

        for subexpr in expr:
            typeExpr.joinType(subexpr.staticType)

        expr.staticType = typeExpr

    Product = _checkJoin
    LeftJoin = _checkJoin

    def preSelect(self, expr):
        # Process the relation subexpression and create a scope from
        # its type.
        self.process(expr[0])
        self.createScope(expr[0].staticType)

        # Now process the condition.
        self.process(expr[1])

        # Remove the scope.
        self.closeScope()

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
        self.createScope(expr[0].staticType)

        # Now process the mapping expressions.
        for mappingExpr in expr[1:]:
            self.process(mappingExpr)

        # Remove the scope.
        self.closeScope()

        return (None,) * len(expr)

    def MapResult(self, expr, rel, *mappingExprs):
        typeExpr = RelationType()
        for colName, colExpr in zip(expr.columnNames, expr[1:]):
            typeExpr.addColumn(colName, colExpr.staticType)
        expr.staticType = typeExpr

    def preStatementResult(self, expr):
        # Process the relation subexpression and create a scope from
        # its type.
        self.process(expr[0])
        self.createScope(expr[0].staticType)

        # Now process the expressions in the statement templates.
        for stmtTmpl in expr[1:]:
            for component in stmtTmpl:
                self.process(component)

        # Remove the scope.
        self.closeScope()

        return (None,) * len(expr)

    def StatementResult(self, expr, rel, *stmtTmpls):
        typeExpr = StatementRelType()
        for i, stmtTmpl in enumerate(expr[1:]):
            if not stmtTmpl[0].staticType.isSubtype(resourceType):
                error(stmtTmpl[0], _("Subject type must be a resource"))
            typeExpr.addColumn('subject%d' % (i + 1),
                               stmtTmpl[0].staticType)

            if not stmtTmpl[1].staticType.isSubtype(resourceType):
                error(stmtTmpl[1], _("Predicate type must be a resource"))
            typeExpr.addColumn('predicate%d' % (i + 1),
                               stmtTmpl[1].staticType)

            if not stmtTmpl[2].staticType.isSubtype(rdfNodeType):
                error(stmtTmpl[2], _("Object type must be an RDF node"))
            typeExpr.addColumn('object%d' % (i + 1),
                               stmtTmpl[2].staticType)
        expr.staticType = typeExpr

    def Distinct(self, expr, subexpr):
        expr.staticType = expr[0].staticType
        
    def OffsetLimit(self, expr, subexpr):
        expr.staticType = expr[0].staticType
        
    def Sort(self, expr, subexpr, orderBy):
        expr.staticType = expr[0].staticType

    def Empty(self, expr):
        # Empty relation type.
        expr.staticType = RelationType()

    def _setOperationType(self, expr, *operands):
        typeExpr = expr[0].staticType
        for subexpr in expr[1:]:
            typeExpr.generalizeType(subexpr.staticType)
            if typeExpr == nullType:
                error(expr, _("Incompatible types in set operation"))
        expr.staticType = typeExpr

    def Union(self, expr, *operands):
        self._setOperationType(expr, *operands)

    def SetDifference(self, expr, operand1, operand2):
        self._setOperationType(expr, operand1, operand2)

    def Intersection(self, expr, *operands):
        self._setOperationType(expr, *operands)

    def Insert(self, expr, stmtRel):
        if not isinstance(expr[0].staticType, StatementRelType):
            error(expr, _("Insert subexpression must be a statement relation"))
        expr.staticType = expr[0].staticType

    def Delete(self, expr, stmtRel):
       if not isinstance(expr[0].staticType, StatementRelType):
            error(expr, _("Delete subexpression must be a statement relation"))
       expr.staticType = expr[0].staticType
       
    def DynType(self, expr, *subexprs):
        expr.staticType = resourceType

    def Lang(self, expr, *subexprs):
        expr.staticType = genericLiteralType
        
    def LangMatches(self, expr, sexpr1, sexpr2):
        self._checkScalarOperands(expr, 'LANG_MATCHES')
        expr.staticType = booleanLiteralType
        

def typeCheck(expr):
    """Type check `expr`. This function sets the ``staticType`` and
    ``failSafe`` fields in all nodes in `expr`. `expr` will be
    modified in place, but the return value must be used since the
    root node may change."""
    checker = TypeChecker()
    checker.process(expr)
    return expr
