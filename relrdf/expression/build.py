class Explicit(object):
    __slots__ = ('wrapped')

    def __init__(self, wrapped):
        self.wrapped = wrapped


def buildExpression(exprIter):
    """Builds an expression from an expression iterable.

    An expression iterable is in iterable object whose first element
    is a constructor function for a expression node and whose
    subsequent elements are intended to define the constructor
    parameters. If such elements are iterable, they will be fed
    recursively to this function in order to build the actual
    parameter value. If they are not iterable, they will be passed
    directly as parameters. In order to pass iterable values directly
    as parameters, they can be wrapped using the `Explicit` class in
    this module."""

    it = iter(exprIter)
    constr = it.next()
    params = list(it)

    for i, p in enumerate(params):
        if isinstance(p, Explicit):
            params[i] = p.wrapped
        elif hasattr(p, '__iter__'):
             params[i] = buildExpression(p)

    return constr(*params)

