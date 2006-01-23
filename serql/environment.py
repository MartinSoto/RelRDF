import StringIO

import antlr

from expression import nodes
from expression import rewrite

import error
import SerQLLexer
import SerQLParser


class ParseEnvironment(object):
    """A parsing environment for SerQL. It contains high level
    operations for obtaining normalized expression trees out of SerQL
    queries."""

    __slots__ = ('prefixes')

    def __init__(self, prefixes={}):
        self.prefixes = prefixes

    def setPrefixes(self, prefixes):
        self.prefixes = prefixes

    def getPrefixes(self):
        return self.prefixes

    def parse(self, queryText, fileName=_("<unknown>")):
        if isinstance(queryText, str):
            stream = StringIO.StringIO(queryText)
        else:
            stream = queryText

        lexer = SerQLLexer.Lexer() 
        lexer.setInput(stream)

        parser = SerQLParser.Parser(lexer, prefixes=self.prefixes)
        parser.setFilename(fileName)

        try:
            expr = parser.query()
        except antlr.RecognitionException, e:
            new = error.SyntaxError.create(e)
            if new:
                new.fileName = fileName
                raise new
            else:
                raise e
        except antlr.TokenStreamRecognitionException, e:
            new = error.SyntaxError.create(e.recog)
            if new:
                new.fileName = fileName
                raise new
            else:
                raise e

        return self.simplifySerQLExpr(expr)

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
