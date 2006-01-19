from serql import SerQLLexer
from serql import SerQLParser

from serql import serql

from tree import expression, rewrite


lexer = SerQLLexer.Lexer() 
parser = SerQLParser.Parser(lexer)
parser.setFilename(lexer.getFilename())

expr = parser.selectQuery()

modif = True
while modif:
    modif = False

    (expr, m) = rewrite.flattenAssoc(expression.Product, expr)
    modif = modif or m
    
    (expr, m) = rewrite.flattenAssoc(expression.Or, expr)
    modif = modif or m
    (expr, m) = rewrite.flattenAssoc(expression.And, expr)
    modif = modif or m
    
    (expr, modif) = rewrite.promoteSelect(expr)
    modif = modif or m
    
    (expr, modif) = rewrite.flattenSelect(expr)
    modif = modif or m

expr.prettyPrint()
