import antlr

from relrdf import commonns, error
from relrdf.expression import literal, uri, nodes

import schema
import sqlnodes
import macro


class Parser(antlr.LLkParser):
    """The base class for the expression parser generated by ANTLR."""

    __slots__ = ('basePrefixes',
                 'externalPrefixes',
                 'localPrefixes',

                 'schema',
                 'mainEnv',)

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
        """Initializes a expression parser object.

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

        # Schema object being defined.
        self.schema = None

        # Main environment (for schema arguments.)
        self.mainEnv = macro.Environment()


    @staticmethod
    def makeTypedLiteral(string, typeUri):
        """Make a `nodes.Literal` expression node with the value given
        by `string` and the data type given by `typeUri`, and return
        it.""" 
        lt = literal.Literal(string, typeUri=typeUri)
        return nodes.Literal(lt)


    def defineLocalPrefix(self, qnameToken, uriToken):
        """Create a new local prefix `prefix` with associated URI
        `uri`."""
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
        qualified name `qname`."""
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
        """Make sure the prefix does not start with `'_'`."""
        return token.getText()

    def createCallExpr(self, name):
        closure = self.schema.getMacro(name)
        if closure is not None:
            return macro.MacroCall(closure)
        else:
            return sqlnodes.SqlFunctionCall(name)