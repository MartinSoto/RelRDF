import nodes
import rewrite


def flattenAssoc(nodeType, expr, subexprsModif):
    i = 0
    while i < len(expr):
        subexpr = expr[i]
        if isinstance(subexpr, nodeType):
            expr[i:i+1] = subexpr
            subexprsModif = True
        i += 1

    return expr, subexprsModif

def promoteSelect(expr, subexprsModif):
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

def flattenSelect(expr, subexprsModif):
    (rel, predicate) = expr
    if not isinstance(rel, nodes.Select):
        return expr, subexprsModif
    else:
        return (nodes.Select(rel[0],
                             nodes.And(rel[1], predicate)),
                True)

def simplifyNode(expr, subexprsModif):
    modif = True
    while modif:
        modif = False

        if isinstance(expr, nodes.Product):
            expr, m = flattenAssoc(nodes.Product, expr, modif)
            modif = modif or m
            expr, m = promoteSelect(expr, modif)
            modif = modif or m
        elif isinstance(expr, nodes.Or):
            expr, m = flattenAssoc(nodes.Or, expr, modif)
            modif = modif or m
        elif isinstance(expr, nodes.And):
            expr, m = flattenAssoc(nodes.And, expr, modif)
            modif = modif or m
        elif isinstance(expr, nodes.Union):
            expr, m = flattenAssoc(nodes.Union, expr, modif)
            modif = modif or m
        elif isinstance(expr, nodes.Intersection):
            expr, m = flattenAssoc(nodes.Intersection, expr, modif)
            modif = modif or m
        elif isinstance(expr, nodes.Select):
            expr, m = flattenSelect(expr, modif)
            modif = modif or m

        subexprsModif = subexprsModif or modif
    
    return expr, subexprsModif

def simplify(expr):
    """Simplify a expression."""

    modif = True
    while modif:
        modif = False
        expr, m = rewrite.exprApply(expr, postOp=simplifyNode)
        modif = modif or m

    return expr

