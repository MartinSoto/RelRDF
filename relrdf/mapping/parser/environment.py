import StringIO

import antlr

from relrdf import error

from relrdf.expression import nodes, rewrite, simplify


import ExpressionLexer
import ExpressionParser


def checkNotSupported(expr):
    if isinstance(expr, nodes.NotSupported):
        new = error.NotSupportedError(expr.getExtents(),
                                      msg=_("This feature is not yet "
                                            "supported. Sorry!"))
        raise new

    for subexpr in expr:
        checkNotSupported(subexpr)


class ParseEnvironment(object):
    """A parsing environment for the internal expression language. It
    contains high level operations for obtaining expression trees out
    of the expression sytax."""

    __slots__ = ('prefixes',)

    def __init__(self, prefixes={}):
        self.prefixes = prefixes

    def setPrefixes(self, prefixes):
        self.prefixes = prefixes

    def getPrefixes(self):
        return self.prefixes

    def parse(self, queryText, fileName=_("<unknown>")):
        if isinstance(queryText, str) or isinstance(queryText, unicode):
            stream = StringIO.StringIO(queryText)
        else:
            stream = queryText

        lexer = ExpressionLexer.Lexer() 
        lexer.setInput(stream)

        parser = ExpressionParser.Parser(lexer, prefixes=self.prefixes)
        parser.setFilename(fileName)

        try:
            expr = parser.expression()
        except antlr.RecognitionException, e:
            new = error.SyntaxError.create(e)
            if new:
                new.extents.fileName = fileName
                raise new
            else:
                raise e
        except antlr.TokenStreamRecognitionException, e:
            new = error.SyntaxError.create(e.recog)
            if new:
                new.extents.fileName = fileName
                raise new
            else:
                raise e

        # Check for use of not implemented features.
        checkNotSupported(expr)

        return expr


if __name__ == '__main__':
    import sys

    env = ParseEnvironment()
    expr = env.parse(sys.stdin)
    expr.prettyPrint()
