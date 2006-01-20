import StringIO

from expression import nodes
from expression import rewrite

import SerQLLexer
import SerQLParser


class ParseEnvironment(object):
    """A parsing environment for SerQL. It contains high level
    operations for obtaining normalized expression trees out of SerQL
    queries."""

    __slots__ = ('lexer',
                 'parser')

    def __init__(self, prefixes={}):
        self.lexer = SerQLLexer.Lexer() 
        self.parser = SerQLParser.Parser(self.lexer, prefixes=prefixes)

    def setPrefixes(self, prefixes):
        self.parser.prefixes = prefixes

    def getPrefixes(self):
        return self.parser.prefixes

    prefixes = property(getPrefixes, setPrefixes)

    def parse(self, queryText, fileName="<unknown>"):
        if isinstance(queryText, str):
            stream = StringIO.StringIO(queryText)
        else:
            stream = queryText

        self.lexer.setInput(stream)
        self.parser.setFilename(fileName)

        return self.simplifySerQLExpr(self.parser.query())

    @staticmethod
    def simplifySerQLExpr(expr):
        """Simplify a expression resulting from parsing a SerQL query."""

        modif = True
        while modif:
            modif = False

            # Flatten associative operators.
            (expr, m) = rewrite.flattenAssoc(nodes.Product, expr)
            modif = modif or m
            (expr, m) = rewrite.flattenAssoc(nodes.Or, expr)
            modif = modif or m
            (expr, m) = rewrite.flattenAssoc(nodes.And, expr)
            modif = modif or m

            # Move selects up in the tree.
            (expr, modif) = rewrite.promoteSelect(expr)
            modif = modif or m

            # Flatten nested selects.
            (expr, modif) = rewrite.flattenSelect(expr)
            modif = modif or m

        return expr
