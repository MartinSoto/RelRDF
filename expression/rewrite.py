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


class ExpressionProcessor(object):
    """A generic processor for expression trees. See the `process`
    method for more details."""

    __slots__ = ()

    def process(self, expr, prePrefix=None, postPrefix=""):
        """Calculate (build) a value from an expression tree `expr` using
        this object's methods.

        Basic operation of this function traverses the expression tree
        in a bottom up fashion, i.e., the subexpressions are processed
        in an undefined order before the expression itself is
        processed. For each expression node in the tree, the method of
        `self` will be fetched whose name is identical to the node's
        class name with the value of `postPrefix` prepended to it (if
        no such method exists, a method with name `postPrefix +
        'Default'` will be used.) The method will be called with the
        expression node and the values already calculated for the
        subexpressions as parameters. The returned value will be
        passed, in the same fashion, to the method invoked for the
        parent node of the expression, or returned by this method
        for the root node.

        In some cases, it is necessary to prevent certain
        subexpressions from being processed, to force a certain order
        for their processing, or to perform additional operations in
        between. If `prePrefix` is not `None`, its value will be
        prepended to each nodes's class name. If there's a method in
        `self` with that name, it will be called before any
        subexpressions of the corresponding node have been processed,
        passing it the node itself as parameter. This method is
        expected to return an iterable object, containing the values
        calculated for the subexpressions of `expr`. The method
        implementation is free to use any algorithm (including calling
        this method recursively) to produce these values."""

        assert isinstance(expr, nodes.ExpressionNode)

        # Calculate the values for the subexpressions.
        if prePrefix is not None and \
               hasattr(self, prePrefix + expr.__class__.__name__):
            # Invoke the preorder method.
            method = getattr(self, prePrefix + expr.__class__.__name__)
            procSubexpr = method(expr)
        else:
            # Process the subexpressions recursively and collect the values.
            procSubexprs = []
            for subexpr in expr:
                procSubexprs.append(self.process(subexpr))

        if hasattr(self, postPrefix + expr.__class__.__name__):
            method = getattr(self, postPrefix + expr.__class__.__name__)
        else:
            method = getattr(self, postPrefix + "Default")

        # Invoke the postorder method.
        return method(expr, *procSubexprs)


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
