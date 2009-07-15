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
from relrdf import typecheck

import simplify


import SparqlLexer
import SparqlParser

import decouple, spqnodes


def checkNotSupported(expr):
    if isinstance(expr, nodes.NotSupported):
        new = error.NotSupportedError(expr.getExtents(),
                                      msg=_("This feature is not yet "
                                            "supported. Sorry!"))
        raise new

    for subexpr in expr:
        checkNotSupported(subexpr)


class ParseEnvironment(object):
    """A parsing environment for SPARQL. It contains high level
    operations for obtaining expression trees out of SPARQL queries."""

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

        lexer = SparqlLexer.Lexer() 
        lexer.setInput(stream)

        parser = SparqlParser.Parser(lexer, prefixes=self.prefixes,
                                     baseUri=fileName)
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

        # Check for use of not implemented features.
        checkNotSupported(expr)

        # Simplify the expression. This includes the standard
        # simplification prescribed by Chapter 12 of the SPARQL spec.
        expr = simplify.simplify(expr)

        # Type check the expression, using the specialized SPARQL type
        # checker.
        expr = typecheck.typeCheck(expr)

        # Decouple the patterns and translate special SPARQL
        # constructs.
        transf = decouple.PatternDecoupler()
        expr = transf.process(expr)

        return expr
