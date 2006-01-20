import sys
import serql

prefixes = {
    'ex': 'http://example.com/model#'
    }

parser = serql.Parser(prefixes)
parser.parse(sys.stdin).prettyPrint()

