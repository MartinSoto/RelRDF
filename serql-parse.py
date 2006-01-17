from serql import SerQLLexer
from serql import SerQLParser

from serql import serql

from tree import expression, rewrite


lexer = SerQLLexer.Lexer() 
parser = SerQLParser.Parser(lexer)
parser.setFilename(lexer.getFilename())

expr = parser.graphPattern()
(flat, modif) = rewrite.flattenAssoc(expression.Product, expr)

flat.prettyPrint()
print "Modified:", modif

(flat, modif) = rewrite.flattenAssoc(expression.Product, flat)
print "Modified:", modif
