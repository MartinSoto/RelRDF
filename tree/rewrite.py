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

def flattenAssoc(nodeType, expr):
    def operation(expr, subexprsModif, *subexprs):
        modif = subexprsModif
        if not isinstance(expr, nodeType):
            flattened = subexprs
        else:
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

    return treeApply(operation, expr)
