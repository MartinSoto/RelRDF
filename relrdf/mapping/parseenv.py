import StringIO

import antlr

from relrdf.localization import _
from relrdf import error

from relrdf.expression import nodes, rewrite, simplify


import SchemaLexer
import SchemaParser


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

    def _parse(self, text, fileName, productionName):
        if isinstance(text, str) or isinstance(text, unicode):
            stream = StringIO.StringIO(text)
        else:
            stream = text

        lexer = SchemaLexer.Lexer() 
        lexer.setInput(stream)

        parser = SchemaParser.Parser(lexer, prefixes=self.prefixes)
        parser.setFilename(fileName)

        try:
            value = getattr(parser, productionName)()
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

        return value

    def parseSchema(self, text, fileName=_("<unknown>")):
        return self._parse(text, fileName, 'schemaDef')

    def parseExpr(self, text, fileName=_("<unknown>")):
        return self._parse(text, fileName, 'expression')


if __name__ == '__main__':
    import sys

    env = ParseEnvironment()
    schema = env.parseExpr(sys.stdin)
