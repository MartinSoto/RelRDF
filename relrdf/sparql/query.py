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
from relrdf.parsequerybase import BaseQuery
from relrdf.util import nsshortener

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


class Query(BaseQuery):
    """A class representing a parsed SPARQL query."""

    __slots__ = ('_expr')

    def __init__(self, queryText, fileName=_("<unknown>"),
                 prefixes=nsshortener.NamespaceUriShortener(),
                 **ignoredArgs):
        if isinstance(queryText, basestring):
            stream = StringIO.StringIO(queryText)
        else:
            stream = queryText

        lexer = SparqlLexer.Lexer()
        lexer.setInput(stream)

        parser = SparqlParser.Parser(lexer, prefixes=prefixes,
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

        # Decouple the patterns and translate especial SPARQL
        # constructs.
        transf = decouple.PatternDecoupler()
        expr = transf.process(expr)

        # Store the final expression in the object.
        self._expr = expr

    def getExpression(self):
        """Retrieve the expression associated to this query.

        Since the expression in a query can be modified, it can be
        retrieved only once safely. Further attempts at retrieving it
        will fail with an assertion error."""
        assert self._expr is not None, \
            "Query expressions can be retrieved only once."
        expr = self._expr
        self._expr = None
        return expr

    def _getDatasetNode(self):
        datasetExpr = self._expr
        while not isinstance(datasetExpr, nodes.Dataset):
            datasetExpr = datasetExpr[0]

        return datasetExpr

    def getDefaultGraphs(self):
        """Retrieve the set of default graph URIs for this query.

        These are the URIs in the FROM clauses in the query, but not
        in the FROM NAMED clauses. The result is an inmutable set of
        URIs."""
        return frozenset((expr.uri for expr in self._getDatasetNode()[1]))

    def getNamedGraphs(self):
        """Retrieve the set of named graph URIs for this query.

        These are the URIs in the FROM NAMED clauses in the query, but
        not in the plain FROM clauses. The result is an inmutable set
        of URIs."""
        return frozenset((expr.uri for expr in self._getDatasetNode()[2]))
