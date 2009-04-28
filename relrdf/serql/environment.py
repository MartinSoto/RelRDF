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

from relrdf.expression import nodes
from relrdf.expression import rewrite

from relrdf import typecheck

import SerQLLexer, SerQLParser, decouple


class ParseEnvironment(object):
    """A parsing environment for SerQL. It contains high level
    operations for obtaining expression trees out of SerQL queries."""

    __slots__ = ('prefixes',)

    def __init__(self, prefixes={}):
        self.prefixes = prefixes

    def setPrefixes(self, prefixes):
        self.prefixes = prefixes

    def getPrefixes(self):
        return self.prefixes

    def parse(self, queryText, fileName=_("<unknown>")):
        if isinstance(queryText, str) or isinstance(queryText, unicode):
            stream = StringIO.StringIO(queryText)
        else:
            stream = queryText

        lexer = SerQLLexer.Lexer() 
        lexer.setInput(stream)

        parser = SerQLParser.Parser(lexer, prefixes=self.prefixes)
        parser.setFilename(fileName)

        try:
            expr = parser.query()
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

        # Type check the expression.
        expr = typecheck.typeCheck(expr)

        # Decouple the patterns.
        transf = decouple.PatternDecoupler()
        expr = transf.process(expr)

        return expr
