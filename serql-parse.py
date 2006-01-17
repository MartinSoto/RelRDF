from serql import SerQLLexer
from serql import SerQLParser

from serql import serql

from tree import expression, rewrite


lexer = SerQLLexer.Lexer() 
parser = SerQLParser.Parser(lexer)
parser.setFilename(lexer.getFilename())

expr = parser.graphPattern()
flat = rewrite.flattenAssoc(expression.Product, expr)

flat.prettyPrint()
