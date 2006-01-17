import expression

def curry(function, arg1):
    def curried(*args, **keywords):
        return function(arg1, *args, **keywords)

    return curried

def treeApply(operation, expr):
    assert isinstance(expr, expression.ExpressionNode)

    procSubexprs = []
    for subexpr in expr.subexprs:
        procSubexprs.append(treeApply(operation, subexpr))

    return operation(expr, *procSubexprs)

def flattenAssoc(nodeType, expr):
    def operation(expr, *subexprs):
        if not isinstance(expr, nodeType):
            return expr.copyNode(*subexprs)
        
        flattened = []
        for subexpr in subexprs:
            if isinstance(subexpr, nodeType):
                flattened.extend(subexpr.subexprs)
            else:
                flattened.append(subexpr)

        return expr.copyNode(*flattened)

    return treeApply(operation, expr)
