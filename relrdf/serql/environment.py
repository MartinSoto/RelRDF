import StringIO

import antlr

from relrdf.localization import _
from relrdf import error

from relrdf.expression import nodes
from relrdf.expression import rewrite

from relrdf import typecheck

import SerQLLexer, SerQLParser, decouple


class ParseEnvironment(object):
    """A parsing environment for SerQL. It contains high level
    operations for obtaining expression trees out of SerQL queries."""

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

        lexer = SerQLLexer.Lexer() 
        lexer.setInput(stream)

        parser = SerQLParser.Parser(lexer, prefixes=self.prefixes)
        parser.setFilename(fileName)

        try:
            expr = parser.query()
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

        # Type check the expression.
        expr = typecheck.typeCheck(expr)

        # Decouple the patterns.
        transf = decouple.PatternDecoupler()
        expr = transf.process(expr)

        return expr
