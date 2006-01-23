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
    if len(sys.argv) > 1:
        query = ''.join(sys.stdin)
        for i in xrange(int(sys.argv[1])):
            parser.parse(query, "sys.stdin")
    else:
        parser.parse(sys.stdin, "sys.stdin").prettyPrint()
except serql.Error, e:
    print >> sys.stderr, "Error:", str(e)
