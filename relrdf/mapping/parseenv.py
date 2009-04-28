# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2009 Fraunhofer-Institut fuer Experimentelles
#                         Software Engineering (IESE).
#
# RelRDF is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA. 


import StringIO

import antlr

from relrdf.localization import _
from relrdf import error

from relrdf.expression import nodes, rewrite, simplify


import SchemaLexer
import SchemaParser


class ParseEnvironment(object):
    """A parsing environment for the internal expression language. It
    contains high level operations for obtaining expression trees out
    of the expression sytax."""

    __slots__ = ('prefixes',)

    def __init__(self, prefixes={}):
        self.prefixes = prefixes

    def setPrefixes(self, prefixes):
        self.prefixes = prefixes

    def getPrefixes(self):
        return self.prefixes

    def _parse(self, text, fileName, productionName):
        if isinstance(text, str) or isinstance(text, unicode):
            stream = StringIO.StringIO(text)
        else:
            stream = text

        lexer = SchemaLexer.Lexer() 
        lexer.setInput(stream)

        parser = SchemaParser.Parser(lexer, prefixes=self.prefixes)
        parser.setFilename(fileName)

        try:
            value = getattr(parser, productionName)()
        except antlr.RecognitionException, e:
            new = error.SyntaxError.create(e)
            if new:
                new.extents.fileName = fileName
                raise new
            else:
                raise e
        except antlr.TokenStreamRecognitionException, e:
            new = error.SyntaxError.create(e.recog)
            if new:
                new.extents.fileName = fileName
                raise new
            else:
                raise e

        return value

    def parseSchema(self, text, fileName=_("<unknown>")):
        return self._parse(text, fileName, 'schemaDef')

    def parseExpr(self, text, fileName=_("<unknown>")):
        return self._parse(text, fileName, 'expression')


if __name__ == '__main__':
    import sys

    env = ParseEnvironment()
    schema = env.parseExpr(sys.stdin)
