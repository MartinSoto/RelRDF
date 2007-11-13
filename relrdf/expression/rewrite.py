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

    __slots__ = ('prePrefix',
                 'postPrefix')

    def __init__(self, prePrefix=None, postPrefix=""):
        self.prePrefix = prePrefix
        self.postPrefix = postPrefix

    def process(self, expr):
        """Calculate (build) a value from an expression tree `expr` using
        this object's methods.

        Basic operation of this function traverses the expression tree
        in a bottom up fashion, i.e., the subexpressions are processed
        in an undefined order before the expression itself is
        processed. For each expression node in the tree, the method of
        `self` will be fetched whose name is identical to the node's
        class name with the value of `self.postPrefix` prepended to it
        (if no such method exists, a method with name
        ``self.postPrefix + 'Default'`` will be used.) The method will
        be called with the expression node and the values already
        calculated for the subexpressions as parameters. The returned
        value will be passed, in the same fashion, to the method
        invoked for the parent node of the expression, or returned by
        this method for the root node.

        In some cases, it is necessary to prevent certain
        subexpressions from being processed, to force a certain order
        for their processing, or to perform additional operations in
        between. If `self.prePrefix` is not `None`, its value will be
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
        if self.prePrefix is not None and \
            hasattr(self, self.prePrefix + expr.__class__.__name__):
            # Invoke the preorder method.
            method = getattr(self, self.prePrefix + expr.__class__.__name__)
            procSubexprs = method(expr)
        else:
            # Process the subexpressions recursively and collect the values.
            procSubexprs = []
            for subexpr in expr:
                procSubexprs.append(self.process(subexpr))

        if hasattr(self, self.postPrefix + expr.__class__.__name__):
            method = getattr(self, self.postPrefix + expr.__class__.__name__)
        else:
            method = getattr(self, self.postPrefix + "Default")

        # Invoke the postorder method.
        return method(expr, *procSubexprs)
    
    def Default(self, expr, *pars):
        assert False, "Processor " + self.__class__.__name__ + " defines no action for " + expr.__class__.__name__ + "!"


class ExpressionTransformer(ExpressionProcessor):
    """A generic tranformer for expression trees. The only difference
    with respect to `ExpressionProcessor` is that the default
    operation expects that the calculated values are transformed
    subexpressions."""

    __slots__ = ()

    def Default(self, expr, *transfSubexprs):
        """Set `transfSubexprs` as the subexpressions of `expr` and
        return `expr`."""
        expr[:] = transfSubexprs
        return expr

