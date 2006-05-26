import StringIO

import antlr

from relrdf import error

from relrdf.expression import nodes, rewrite, simplify


import SparqlLexer
import SparqlParser

import typecheck
import decouple, spqnodes


def simplifyNode(expr, subexprsModif):
    modif = True
    while modif:
        modif = False

        if isinstance(expr, spqnodes.GraphPattern):
            expr, m = simplify.flattenAssoc(spqnodes.GraphPattern, expr)
            modif = modif or m

        subexprsModif = subexprsModif or modif
    
    return expr, subexprsModif

def simplifyParseTree(expr):
    """Perform early simplification on a SPARQL parse tree."""

    modif = True
    while modif:
        modif = False
        expr, m = rewrite.exprApply(expr, postOp=simplifyNode)
        modif = modif or m

    return expr


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

        parser = SparqlParser.Parser(lexer, prefixes=self.prefixes)
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

        # Simplify the tree.
        expr = simplifyParseTree(expr)

        # Type check the expression, using the specialized SPARQL type
        # checker.
        expr = typecheck.sparqlTypeCheck(expr)

        # Decouple the patterns and translate special SPARQL
        # constructs.
        transf = decouple.PatternDecoupler()
        expr = transf.process(expr)

        return expr
