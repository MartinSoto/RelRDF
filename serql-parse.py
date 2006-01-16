from serql import SerQLLexer
from serql import SerQLParser

from serql import serql

lexer = SerQLLexer.Lexer() 
parser = SerQLParser.Parser(lexer)
parser.setFilename(lexer.getFilename())

parser.graphPattern().prettyPrint()
