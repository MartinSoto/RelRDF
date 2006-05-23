from relrdf.expression import nodes


class GraphPattern(nodes.ExpressionNode):
    """An expression node representing an SPARQL graph pattern."""

    __slots__ = ()


class OpenUnion(nodes.ExpressionNode):
    """An expression node representing an SPARQL "open" (without fixed
    columns) pattern union operation."""

    __slots__ = ()


class Optional(nodes.ExpressionNode):
    """An expression node representing an SPARQL optional pattern."""

    __slots__ = ()

    def __init__(self, pattern):
        super(Optional, self).__init__(pattern)


class Filter(nodes.ExpressionNode):
    """An expression node representing an SPARQL filter."""

    __slots__ = ()

    def __init__(self, cond):
        super(Filter, self).__init__(cond)


