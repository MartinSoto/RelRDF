import nodes

def curry(function, arg1):
    def curried(*args, **keywords):
        return function(arg1, *args, **keywords)

    return curried

def treeApply(operation, expr):
    assert isinstance(expr, nodes.ExpressionNode)

    subexprsModif = False
    for i, subexpr in enumerate(expr):
        (expr[i], modif) = treeApply(operation, subexpr)
        subexprsModif = subexprsModif or modif

    return operation(expr, subexprsModif)

def treeApplyObject(object, expr):
    assert isinstance(expr, nodes.ExpressionNode)

    procSubexprs = []
    for subexpr in expr:
        procSubexprs.append(treeApplyObject(object, subexpr))

    if hasattr(object, expr.__class__.__name__):
        method = getattr(object, expr.__class__.__name__)
        return method(expr, *procSubexprs)
    else:
        return tuple([expr,] + procSubexprs)

def treeMatchApply(nodeType, operation, expr):
    def operationWrapper(expr, subexprsModif):
        if not isinstance(expr, nodeType):
            return (expr, subexprsModif)
        else:
            return operation(expr, subexprsModif)

    return treeApply(operationWrapper, expr)

def flattenAssoc(nodeType, expr):
    def operation(expr, subexprsModif):
        i = 0
        for subexpr in expr:
            if isinstance(subexpr, nodeType):
                expr[i:i+1] = subexpr
                i += len(expr)
                subexprsModif = True
            else:
                i += 1

        return expr, subexprsModif

    return treeMatchApply(nodeType, operation, expr)

def promoteSelect(expr):
    def operation(expr, subexprsModif):
        assert isinstance(expr, nodes.Product)

        promoted = []
        conditions = []
        for subexpr in expr:
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
    def operation(expr, subexprsModif):
        (rel, predicate) = expr
        if not isinstance(rel, nodes.Select):
            return expr, subexprsModif
        else:
            return (nodes.Select(rel[0],
                                 nodes.And(rel[1], predicate)),
                    True)

    return treeMatchApply(nodes.Select, operation, expr)
