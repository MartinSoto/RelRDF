import StringIO

from tree import expression


class Var(expression.ExpressionNode):
    """An expression node representing a SerQL variable by name."""

    __slots = ('name')

    def __init__(self, name):
        super(Var, self).__init__()

        self.name = name

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' %s' % self.name)


class Query(object):
    """The representation of a SerQl query."""

    __slots__ = ('vars',
                 'prefixes')

    def __init__(self):
        self.vars = {}
        self.prefixes = {}

    def getVariable(self, varName):
        try:
            return self.vars[varName]
        except KeyError:
            var = Var(varName)
            self.vars[varName] = var

            return var

    def setPrefix(self, prefix, uri):
        self.prefixes[prefix] = uri

    def getPrefixUri(self, prefix):
        return self.prefixes[prefix]
        # FIXME: Produce appropriate exception.

    def getPrefixes(self):
        return self.prefixes

    def resolveQName(self, qName):
        pos = qName.index(':')
        base = self.getPrefixUri(qName[:pos])
        return base + qName[pos + 1:]

    def __repr__(self):
        s = StringIO.StringIO()

        # FIXME: Put something here.

        return s.getvalue()
