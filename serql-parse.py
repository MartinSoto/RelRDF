import sys

# Activate the _() function.
import gettext
gettext.install('relrdf')

import serql


prefixes = {
    'ex': 'http://example.com/model#'
    }

parser = serql.Parser(prefixes)

try:
    parser.parse(sys.stdin, "sys.stdin").prettyPrint()
except serql.Error, e:
    print >> sys.stderr, "Error:", str(e)
