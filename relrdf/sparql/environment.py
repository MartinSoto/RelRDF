import StringIO

import antlr

from relrdf.localization import _
from relrdf import error

from relrdf.expression import nodes, rewrite, simplify


import SparqlLexer
import SparqlParser

import typecheck
import decouple, spqnodes


def checkNotSupported(expr):
    if isinstance(expr, nodes.NotSupported):
        new = error.NotSupportedError(expr.getExtents(),
                                      msg=_("This feature is not yet "
                                            "supported. Sorry!"))
        raise new

    for subexpr in expr:
        checkNotSupported(subexpr)


class ParseEnvironment(object):
    """A parsing environment for SPARQL. It contains high level
    operations for obtaining expression trees out of SPARQL queries."""

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

        lexer = SparqlLexer.Lexer() 
        lexer.setInput(stream)

        parser = SparqlParser.Parser(lexer, prefixes=self.prefixes, baseUri=fileName)
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

        # Check for use of not implemented features.
        checkNotSupported(expr)

        # Type check the expression, using the specialized SPARQL type
        # checker.
        expr = typecheck.sparqlTypeCheck(expr)

        # Decouple the patterns and translate special SPARQL
        # constructs.
        transf = decouple.PatternDecoupler()
        expr = transf.process(expr)

        return expr
