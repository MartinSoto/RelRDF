import sys

# Activate the _() function.
import gettext
gettext.install('relrdf')

import serql
from sqlmap import map
from sqlmap import generate


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
        expr = parser.parse(sys.stdin, "sys.stdin")
        expr.prettyPrint()
        print

        #mapper = map.VersionMapper(17)
        mapper = map.MultiVersionMapper('http://ex.com/versions#')
        expr = mapper.mapExpression(expr)
        expr.prettyPrint()
        print

        print generate.generate(expr)
except serql.Error, e:
    print >> sys.stderr, "Error:", str(e)
