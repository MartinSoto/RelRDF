import antlr

from relrdf.localization import _
from relrdf import commonns, error
from relrdf.expression import literal, uri, nodes, util
from relrdf.commonns import fn, xsd

class Parser(antlr.LLkParser):
    """The base class for the SPARQL parser generated by ANTLR."""

    __slots__ = ('basePrefixes',
                 'externalPrefixes',
                 'localPrefixes',
                 'variables',
                 'blankNodes')

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
        
        # The set of used variable names, in order they first appeared
        self.variables = []
        
        # Map of blank node labels to the actual resource objects
        self.blankNodes = {}
        
    @staticmethod
    def makeTypedLiteral(string, typeUri):
        """Make a `nodes.Literal` expression node with the value given
        by `string` and the data type given by `typeUri`, and return
        it.""" 
        lt = literal.Literal(string, typeUri=typeUri)
        return nodes.Literal(lt)
    
    def makeIsResource(self, expr, blank):
        """Return an expression that will evaluate to true if given expression
        is a resource (URI or blank node, respectively)"""
        
        # Resources are identified by type URI, blank nodes by prefix (see emitter)
        typeExpr = nodes.Equal(nodes.DynType(expr), nodes.Uri(commonns.rdfs.Resource))
        blankExpr = nodes.IsBlankNode(expr.copy())
        
        if blank:
            return nodes.And(typeExpr, blankExpr)
        else:
            return nodes.And(typeExpr, nodes.Not(blankExpr))

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

    def blankNodeByLabel(self, label):
        
        # Try to return the existing blank node
        try:
            return self.blankNodes[label]
        except KeyError:
            # And if that fails, create a new one
            node = util.VarMaker.makeBlank()
            self.blankNodes[label] = node
            return node
    
    def makeCollectionPattern(self, graph, pattern, collection):
        
        assert len(collection) > 0
        
        # Create linked list
        current = head = None
        for item in collection:
            
            # Create new blank node for this collection item            
            #new = nodes.Uri(uri.newBlank())
            new = util.VarMaker.makeBlank()
            
            # Link the node
            if head is None:
                current = head = new
            else:
                
                restTriple = (current.copy(), nodes.Uri(commonns.rdf.rest), new.copy())
                restPattern = nodes.StatementPattern(graph.copy(), *restTriple)
                pattern.append(restPattern)
                
                current = new
        
            # Set the value of this node
            firstTriple = (current, nodes.Uri(commonns.rdf.first), item)
            firstPattern = nodes.StatementPattern(graph.copy(), *firstTriple)
            pattern.append(firstPattern)
        
        # Terminate
        restTriple = (current.copy(), nodes.Uri(commonns.rdf.rest), nodes.Uri(commonns.rdf.nil))
        restPattern = nodes.StatementPattern(graph.copy(), *restTriple)
        pattern.append(restPattern)
        
        # Return the head node
        return head.copy()
    
    CONS_FUNCS = (commonns.xsd.boolean,
                  commonns.xsd.double,
                  commonns.xsd.float,
                  commonns.xsd.decimal,
                  commonns.xsd.integer,
                  commonns.xsd.dateTime,
                  commonns.xsd.string,
                  )
    
    def _makeFunctionCall(self, uri, extents):
        
        # Constructor function?
        if uri in self.CONS_FUNCS:
            return nodes.Cast(uri)
        
        # Unknown function...
        raise error.SyntaxError(msg=_("Unknown function '%s'" % uri),
                                extents=extents)
        
    