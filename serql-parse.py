import sys

# Activate the _() function.
import gettext
gettext.install('relrdf')

import error
import serql
from sqlmap import map
from sqlmap import generate


prefixes = {
    'ex': 'http://example.com/model#'
    }

parser = serql.Parser(prefixes)

try:
    expr = parser.parse(sys.stdin, "sys.stdin")
    expr.prettyPrint()

    #mapper = map.VersionMapper(1)
    #mapper = map.MultiVersionMapper('http://ex.com/versions#')
    #expr = mapper.mapExpression(expr)
    #expr.prettyPrint()
    #print

    #print generate.generate(expr)
except error.Error, e:
    print >> sys.stderr, "Error:", str(e)
