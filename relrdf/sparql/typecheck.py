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


from relrdf.expression import nodes

from relrdf.typecheck import check
from relrdf.typecheck.typeexpr import nullType, rdfNodeType, \
     LiteralType, booleanLiteralType, genericLiteralType, ResourceType, \
     resourceType, RelationType

import spqnodes


class SparqlTypeChecker(check.TypeChecker):
    """A specialized type checker for SPARQL."""

    def preGraphPattern(self, expr):
        # Create an empty scope.
        typeExpr = RelationType()
        self.createScope(typeExpr)

        # Check simple triple patterns and join their types to the
        # current scope.
        for i, subexpr in enumerate(expr):
            if isinstance(subexpr, nodes.StatementPattern):
                self.process(subexpr)
                typeExpr.joinType(subexpr.staticType)

        # Check everything else except filters, and join their types
        # to the current scope.
        for i, subexpr in enumerate(expr):
            if not isinstance(subexpr, spqnodes.Filter) and \
               not isinstance(subexpr, nodes.StatementPattern) :
                self.process(subexpr)
                typeExpr.joinType(subexpr.staticType)

        # Check the filters.
        for i, subexpr in enumerate(expr):
            if isinstance(subexpr, spqnodes.Filter):
                self.process(subexpr)

        # Remove the scope and use it as type for the expression.
        expr.staticType = self.closeScope()

        return (None,) * len(expr)

    def GraphPattern(self, expr, *subexprs):
        # Everything is done in the "pre" method
        pass

    def Optional(self, expr, pattern):
        expr.staticType = expr[0].staticType

    def Filter(self, expr, cond):
        expr.staticType = expr[0].staticType


def sparqlTypeCheck(expr):
    """Type check `expr`. This function sets the ``staticType`` fields
    in all nodes in `expr`. `expr` will be modified in place, but the
    return value must be used since the root node may change."""
    checker = SparqlTypeChecker()
    checker.process(expr)
    return expr

