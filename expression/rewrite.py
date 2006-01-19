import nodes

def curry(function, arg1):
    def curried(*args, **keywords):
        return function(arg1, *args, **keywords)

    return curried

def treeApply(operation, expr):
    assert isinstance(expr, nodes.ExpressionNode)

    subexprsModif = False
    procSubexprs = []
    for subexpr in expr.subexprs:
        (procSubexpr, modif) = treeApply(operation, subexpr)
        procSubexprs.append(procSubexpr)
        subexprsModif = subexprsModif or modif

    return operation(expr, subexprsModif, *procSubexprs)

def remakeExpr(expr, subexprsModif, *subexprs):
    if not subexprsModif:
        return expr, False
    else:
        return expr.copyNode(*subexprs), True

def treeMatchApply(nodeType, operation, expr):
    def operationWrapper(expr, subexprsModif, *subexprs):
        if not isinstance(expr, nodeType):
            return remakeExpr(expr, subexprsModif, *subexprs)
        else:
            return operation(expr, subexprsModif, *subexprs)

    return treeApply(operationWrapper, expr)

def flattenAssoc(nodeType, expr):
    def operation(expr, subexprsModif, *subexprs):
        flattened = []
        for subexpr in subexprs:
            if isinstance(subexpr, nodeType):
                flattened.extend(subexpr.subexprs)
                subexprsModif = True
            else:
                flattened.append(subexpr)

        return remakeExpr(expr, subexprsModif, *flattened)

    return treeMatchApply(nodeType, operation, expr)

def promoteSelect(expr):
    def operation(expr, subexprsModif, *subexprs):
        assert isinstance(expr, nodes.Product)

        promoted = []
        conditions = []
        for subexpr in subexprs:
            if isinstance(subexpr, nodes.Select):
                promoted.append(subexpr[0])
                conditions.append(subexpr[1])
                subexprsModif = True
            else:
                promoted.append(subexpr)

        if subexprsModif:
            return (nodes.Select(nodes.Product(*promoted),
                                 nodes.And(*conditions)),
                    True)

        else:
            return expr, False

    return treeMatchApply(nodes.Product, operation, expr)

def flattenSelect(expr):
    def operation(expr, subexprsModif, rel, predicate):
        if not isinstance(rel, nodes.Select):
            return remakeExpr(expr, subexprsModif, rel, predicate)
        else:
            return (nodes.Select(rel[0],
                                 nodes.And(rel[1], predicate)),
                    True)

    return treeMatchApply(nodes.Select, operation, expr)
