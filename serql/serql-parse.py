import SerQLLexer
import SerQLParser

lexer = SerQLLexer.Lexer() 
parser = SerQLParser.Parser(lexer)
parser.setFilename(lexer.getFilename())

parser.graphPattern()
