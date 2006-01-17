import expression

def curry(function, arg1):
    def curried(*args, **keywords):
        return function(arg1, *args, **keywords)

    return curried

def treeApply(operation, expr):
    assert isinstance(expr, expression.ExpressionNode)

    subexprsModif = False
    procSubexprs = []
    for subexpr in expr.subexprs:
        (procSubexpr, modif) = treeApply(operation, subexpr)
        procSubexprs.append(procSubexpr)
        subexprsModif = subexprsModif or modif

    return operation(expr, subexprsModif, *procSubexprs)

def treeMatchApply(nodeType, operation, expr):
    def operationWrapper(expr, subexprsModif, *subexprs):
        if not isinstance(expr, nodeType):
            if subexprsModif:
                return expr.copyNode(*subexprs), True
            else:
                return expr, False
        else:
            return operation(expr, subexprsModif, *subexprs)

    return treeApply(operationWrapper, expr)

def flattenAssoc(nodeType, expr):
    def operation(expr, subexprsModif, *subexprs):
        modif = subexprsModif
        flattened = []
        for subexpr in subexprs:
            if isinstance(subexpr, nodeType):
                flattened.extend(subexpr.subexprs)
                modif = True
            else:
                flattened.append(subexpr)

        if modif:
            return expr.copyNode(*flattened), True
        else:
            return expr, False

    return treeMatchApply(nodeType, operation, expr)
