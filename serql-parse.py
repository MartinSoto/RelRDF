import sys

# Activate the _() function.
import gettext
gettext.install('relrdf')

import error
import serql
from expression import rewrite
from sqlmap import map
from sqlmap import generate


prefixes = {
    'ex': 'http://example.com/model#'
    }

parser = serql.Parser(prefixes)

try:
    expr = parser.parse(sys.stdin, "sys.stdin")
    #expr.prettyPrint()

    mapper = map.AbstractSqlMapper()
    expr = mapper.process(expr)

    mapper = map.VersionMapper(27)
    #mapper = map.MultiVersionMapper('http://ex.com/versions#')
    expr = mapper.process(expr)
    expr.prettyPrint()

    print
    print generate.generate(rewrite.simplify(expr))
except error.Error, e:
    print >> sys.stderr, "Error:", str(e)
