import StringIO

import antlr

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

    def parse(self, queryText, fileName=_("<unknown>")):
        if isinstance(queryText, str) or isinstance(queryText, unicode):
            stream = StringIO.StringIO(queryText)
        else:
            stream = queryText

        lexer = SchemaLexer.Lexer() 
        lexer.setInput(stream)

        parser = SchemaParser.Parser(lexer, prefixes=self.prefixes)
        parser.setFilename(fileName)

        try:
            parser.main()
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

        return parser.schema


if __name__ == '__main__':
    import sys

    env = ParseEnvironment()
    schema = env.parse(sys.stdin)

    # FIXME: Create a real test routine.
    mapper = schema.getMapper('testMapping', a=3)

    expr = mapper.replStatementPattern(nodes. \
                                       StatementPattern(nodes.Var('a'),
                                                        nodes.Var('b'),
                                                        nodes.Var('c'),
                                                        nodes.Var('d')))
    expr.prettyPrint()
    print '---------------'

    expr = mapper.replStatementPattern(nodes. \
                                       StatementPattern(nodes.Var('a'),
                                                        nodes.Var('b'),
                                                        nodes.Uri('http://xxx'),
                                                        nodes.Var('d')))
    expr.prettyPrint()
    print '---------------'
