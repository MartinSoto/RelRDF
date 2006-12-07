"""Utility operations to work with constant nodes (nodes.Literal or
nodes.Uri) and lists of constant nodes."""

import nodes


def isConstNode(expr):
    return isinstance(expr, nodes.Uri) or \
           isinstance(expr, nodes.Literal)

def constValue(expr):
    if isinstance(expr, nodes.Uri):
        return expr.uri
    elif isinstance(expr, nodes.Literal):
        return expr.literal.value
    return None

def constValues(exprs, all=False):
    for expr in exprs:
        if isinstance(expr, nodes.Uri):
            yield expr.uri
        elif isinstance(expr, nodes.Literal):
            yield expr.literal.value
        elif all:
            raise ValueError

def nonConstExprs(exprs):
    for expr in exprs:
        if not isConstNode(expr):
            yield expr
