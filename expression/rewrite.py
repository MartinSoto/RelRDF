import nodes

def curry(function, arg1):
    def curried(*args, **keywords):
        return function(arg1, *args, **keywords)

    return curried

def exprApply(expr, preOp=None, postOp=None):
    assert isinstance(expr, nodes.ExpressionNode)

    modif = False

    if preOp != None:
        expr, modif = preOp(expr)

    for i, subexpr in enumerate(expr):
        expr[i], m = exprApply(subexpr, preOp, postOp)
        modif = modif or m

    if postOp != None:
        return postOp(expr, modif)
    else:
        return expr, modif

def exprMatchApply(expr, nodeType, preOp=None, postOp=None):
    if preOp != None:
        def preOpWrapper(expr):
            if not isinstance(expr, nodeType):
                return expr, False
            else:
                return preOp(expr)
    else:
        preOpWrapper = None

    if postOp != None:
        def postOpWrapper(expr, subexprsModif):
            if not isinstance(expr, nodeType):
                return expr, subexprsModif
            else:
                return postOp(expr, subexprsModif)
    else:
        postOpWrapper = None

    return exprApply(expr, preOp=preOpWrapper, postOp=postOpWrapper)

def mapObject(object, expr):
    assert isinstance(expr, nodes.ExpressionNode)

    procSubexprs = []
    for subexpr in expr:
        procSubexprs.append(mapObject(object, subexpr))

    if hasattr(object, expr.__class__.__name__):
        method = getattr(object, expr.__class__.__name__)
        return method(expr, *procSubexprs)
    else:
        return tuple([expr,] + procSubexprs)


def flattenAssoc(nodeType, expr):
    def postOp(expr, subexprsModif):
        i = 0
        while i < len(expr):
            subexpr = expr[i]
            if isinstance(subexpr, nodeType):
                expr[i:i+1] = subexpr
                i += len(subexpr)
                subexprsModif = True
            else:
                i += 1

        return expr, subexprsModif

    return exprMatchApply(expr, nodeType, postOp=postOp)

def promoteSelect(expr):
    def postOp(expr, subexprsModif):
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

    return exprMatchApply(expr, nodes.Product, postOp=postOp)

def flattenSelect(expr):
    def postOp(expr, subexprsModif):
        (rel, predicate) = expr
        if not isinstance(rel, nodes.Select):
            return expr, subexprsModif
        else:
            return (nodes.Select(rel[0],
                                 nodes.And(rel[1], predicate)),
                    True)

    return exprMatchApply(expr, nodes.Select, postOp=postOp)

def simplify(expr):
    """Simplify a expression."""

    modif = True
    while modif:
        modif = False

        # Flatten associative operators.
        (expr, m) = flattenAssoc(nodes.Product, expr)
        modif = modif or m
        (expr, m) = flattenAssoc(nodes.Or, expr)
        modif = modif or m
        (expr, m) = flattenAssoc(nodes.And, expr)
        modif = modif or m
        (expr, m) = flattenAssoc(nodes.Union, expr)
        modif = modif or m
        (expr, m) = flattenAssoc(nodes.Intersection, expr)
        modif = modif or m

        # Move selects up in the tree.
        (expr, m) = promoteSelect(expr)
        modif = modif or m

        # Flatten nested selects.
        (expr, m) = flattenSelect(expr)
        modif = modif or m

    return expr
