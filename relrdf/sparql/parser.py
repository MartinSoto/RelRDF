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


import antlr

from relrdf.localization import _
from relrdf import commonns, error
from relrdf.expression import literal, uri, nodes


class Parser(antlr.LLkParser):
    """The base class for the SPARQL parser generated by ANTLR."""

    __slots__ = ('basePrefixes',
                 'externalPrefixes',
                 'localPrefixes')

    # A number of namespace prefixes offered by default by this
    # implementation.
    implBasePrefixes = {
        'rdf': commonns.rdf,
        'rdfs': commonns.rdfs,
        'xsd': commonns.xsd,
        'owl': commonns.owl,
        'serql': commonns.serql,
        'relrdf': commonns.relrdf}


    def __init__(self, *args, **kwargs):
        """Initializes a SPARQL Parser object.

        Recognized keyword arguments (other arguments will be silently
        ignored):

        'prefixes': a dictionary containing predefined namespace
        prefix bindings intended to be used in addition to the
        base, implementation defined prefixes.

        'noBasePrefixes': If `True`, do not define any base namespace
        prefixes.
        """
        super(Parser, self).__init__(*args, **kwargs)

        if kwargs.get('noBasePrefixes', False):
            self.basePrefixes = {}
        else:
            self.basePrefixes = self.implBasePrefixes

        try:
            self.externalPrefixes = kwargs['prefixes']
        except KeyError:
            self.externalPrefixes = {}

        # The set of locally defined namespace prefixes (prefixes
        # defined by the query itself through PREFIX clauses.)
        self.localPrefixes = {}


    @staticmethod
    def makeTypedLiteral(string, typeUri):
        """Make a `nodes.Literal` expression node with the value given
        by `string` and the data type given by `typeUri`, and return
        it.""" 
        lt = literal.Literal(string, typeUri=typeUri)
        return nodes.Literal(lt)


    def defineLocalPrefix(self, qnameToken, uriToken):
        """Create a new local prefix from the token `qnameToken` with
        associated URI obtained from `uriToken`."""
        # Make sure that the prefix is really a prefix. This is hard
        # to check directly with the Antlr parser, at least when the
        # rules are kept close to the SPARQL standard.
        qname = qnameToken.getText()
        if qname.index(':') != len(qname) - 1:
            extents = nodes.NodeExtents()
            extents.setFromToken(qnameToken, self)
            raise error.SyntaxError(msg=_("Invalid namespace prefix '%s'" %
                                          qname),
                                    extents=extents)

        self.localPrefixes[qname[:-1]] = \
            uri.Namespace(uriToken.getText())

    def getPrefixUri(self, prefix):
        """Return the uri.Namespace object associated to namespace
        prefix `prefix`.

        Prefixes will be searched for first in the locally defined
        set, then in the external set provided when constructing the
        parser object, and finally in the predefined base set.

        A `KeyError` will be raised if the given prefix is not found."""
        try:
            return self.localPrefixes[prefix]
        except KeyError:
            try:
                return uri.Namespace(self.externalPrefixes[prefix])
            except KeyError:
                return self.basePrefixes[prefix]

    def resolveQName(self, qnameToken):
        """Create an URI expression node corresponding to the
        qualified name `qnameToken`."""
        qname = qnameToken.getText()
        try:
            pos = qname.index(':')
            namespace = self.getPrefixUri(qname[:pos])
            expr = nodes.Uri(namespace[qname[pos + 1:]])
            expr.setExtentsFromToken(qnameToken, self)
            return expr
        except KeyError:
            extents = nodes.NodeExtents()
            extents.setFromToken(qnameToken)
            raise error.SemanticError(
                msg=_("Undefined namespace prefix '%s'") % \
                qname[:qname.index(':')],
                extents=extents)

    def checkDefinedPrefix(self, token):
        """Make sure the prefix does not start with ``'_'``."""
        return token.getText()

    def makeStmtTemplates(self, graphPattern):
        """Make a list of statement templates from a graph pattern.

        The graph pattern must be a flat list of statement
        patterns. This method is used to build the statement templates
        in a 'construct' statement.
        """
        result = []
        for stmtPattern in graphPattern:
            assert isinstance(stmtPattern, nodes.StatementPattern)
            result.append(nodes.StatementTemplate(*stmtPattern[1:]))

        return result

    def makeModifQuery(self, cls, graphUri, where, *templates):
        if where is None:
            where = nodes.Empty()
        cons = nodes.StatementResult(where, *templates)
        if graphUri is not None:
            return cls(graphUri.uri, cons)
        else:
            return cls(None, cons)
