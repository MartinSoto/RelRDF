header {
    from relrdf.commonns import rdf, xsd
    from relrdf.expression import nodes

    import parser, spqnodes
}

options {
    language = "Python";
}

/*----------------------------------------------------------------------
 * Parser
 *--------------------------------------------------------------------*/

class SparqlParser extends Parser("parser.Parser");

options {
    defaultErrorHandler=false;
}

query returns [expr]
    :   prolog
        (   expr=selectQuery
        |   constructQuery
        |   describeQuery
        |   askQuery
        )
    ;

prolog
    :   ( baseDecl )?
        ( prefixDecl )*
    ;

baseDecl
    :   BASE Q_IRI_REF
    ;

prefixDecl
    :   PREFIX qn:QNAME uri:Q_IRI_REF
        { self.defineLocalPrefix(qn, uri) }
    ;

selectQuery returns [expr]
    :   SELECT
        ( DISTINCT )?
        (   { vars=[] }
            (   var=var
                { vars.append(var) }
            )+
        |   TIMES
        )
        ( datasetClause )*
        where=whereClause
        solutionModifier
        { expr = nodes.MapResult([var.name for var in vars], where,
                                 *vars) }
    ;

constructQuery
    :   CONSTRUCT
        constructTemplate
        ( datasetClause )*
        where=whereClause
        solutionModifier
    ;

describeQuery
    :   DESCRIBE
        ( ( varOrIriRef )+ | TIMES )
        ( datasetClause )*
        ( where=whereClause )?
        solutionModifier
    ;

askQuery
    :   ASK
        ( datasetClause )*
        where=whereClause
    ;

datasetClause
    :   FROM
        (   defaultGraphClause
        |   namedGraphClause
        )
    ;

defaultGraphClause
    :   sourceSelector
    ;

namedGraphClause
    :   NAMED source=sourceSelector
    ;

sourceSelector returns [expr]
    :   expr=iriRef
    ;

whereClause returns [expr]
    :   ( WHERE )?
        expr=groupGraphPattern[nodes.Joker()]
    ;

solutionModifier
    :   ( orderClause )?
        ( limitClause )?
        ( offsetClause )?
    ;

orderClause
    :   ORDER BY ( orderCondition )+
    ;

orderCondition
    :   ( ( ASC | DESC ) brackettedExpression )
    |   ( functionCall | var | brackettedExpression )
    ;

limitClause
    :   LIMIT INTEGER
    ;

offsetClause
    :   OFFSET INTEGER
    ;

groupGraphPattern[graph] returns [expr]
    :   { expr = spqnodes.GraphPattern() }
        LBRACE graphPattern[graph, expr] RBRACE
    ;

graphPattern[graph, pattern]
    :   filteredBasicGraphPattern[graph, pattern]
        (   expr=graphPatternNotTriples[graph]
            { pattern.append(expr) }
            ( DOT )?
            graphPattern[graph, pattern]
        )?
    ;

filteredBasicGraphPattern[graph, pattern]
    :   ( blockOfTriples[graph, pattern] )?
        (   constr=constraint
            { pattern.append(constr)  }
            ( DOT )?
            filteredBasicGraphPattern[graph, pattern]
        )?
    ;

blockOfTriples[graph, pattern]
    :   triplesSameSubject[graph, pattern]
        ( DOT ( triplesSameSubject[graph, pattern] )? )*
    ;

graphPatternNotTriples[graph] returns [expr]
    :   expr=optionalGraphPattern[graph]
    |   expr=groupOrUnionGraphPattern[graph]
    |   expr=graphGraphPattern
    ;

optionalGraphPattern[graph] returns [expr]
    :   OPTIONAL pattern=groupGraphPattern[graph]
        { expr = spqnodes.Optional(pattern) }
    ;

graphGraphPattern returns [expr]
    :   GRAPH graph=varOrBlankNodeOrIriRef
        expr=groupGraphPattern[graph]
    ;

groupOrUnionGraphPattern[graph] returns [expr]
    :   expr=groupGraphPattern[graph]
        (   { expr=spqnodes.OpenUnion(expr) }
            (   UNION pattern=groupGraphPattern[graph]
                { expr.append(pattern) }
            )+
        )?
    ;

constraint returns [expr]
    :   FILTER
        (   cond=brackettedExpression
        |   cond=builtInCall
        |   cond=functionCall
        )
        { expr = spqnodes.Filter(cond) }
    ;

functionCall returns [expr]
    :   name=iriRef
        { expr = nodes.FunctionCall(name) }
        argList[expr]
    ;

argList[funcCall]
    :   (   NIL
        |   LPAREN param=expression
            { funcCall.append(param) }
            (    COMMA param=expression
                { funcCall.append(param) }
            )*
            RPAREN
        )
    ;

constructTemplate
    :   LBRACE constructTriples RBRACE
    ;

constructTriples
    :   ( triplesSameSubject ( DOT constructTriples )? )?
    ;

triplesSameSubject[graph, pattern]
    :   subject=varOrTerm propertyListNotEmpty[graph, pattern, subject]
    |   subject=triplesNode propertyList[graph, pattern, subject]
    ;

propertyList[graph, pattern, subject]
    :   ( propertyListNotEmpty[graph, pattern, subject] )?
    ;

propertyListNotEmpty[graph, pattern, subject]
    :   predicate=verb
        objectList[graph, pattern, subject, predicate]
        ( SEMICOLON propertyList[graph, pattern, subject] )?
    ;

objectList[graph, pattern, subject, predicate]
    :   obj=graphNode
        { pattern.append(nodes.StatementPattern(graph.copy(),
                                                subject.copy(),
                                                predicate.copy(),
                                                obj.copy())) }
        ( COMMA objectList[graph, pattern, subject, predicate] )?
    ;

verb returns [expr]
    :   expr=varOrIriRef
    |   RDF_TYPE_ABBREV
        { expr=nodes.Uri(rdf.type) }
    ;

triplesNode returns [expr]
    :   expr=collection
    |   expr=blankNodePropertyList
    ;

blankNodePropertyList returns [expr]
    :   LBRACKET propertyListNotEmpty RBRACKET
        { expr = nodes.NotSupported(); }
    ;

collection returns [expr]
    :   LPAREN ( node=graphNode )+ RPAREN
        { expr = nodes.NotSupported(); }
    ;

graphNode returns [expr]
    :   expr=varOrTerm
    |   expr=triplesNode
    ;

varOrTerm returns [expr]
    :   expr=var
    |   expr=graphTerm
    ;

varOrIriRef returns [expr]
    :   expr=var
    |   expr=iriRef
    ;

varOrBlankNodeOrIriRef returns [expr]
    :   expr=var
    |   expr=blankNode
    |   expr=iriRef
    ;

var returns [expr]
    :   v1:VAR1
        { expr = nodes.Var(v1.getText()); \
          expr.setExtentsFromToken(v1, self) }
    |   v2:VAR2
        { expr = nodes.Var(v2.getText()); \
          expr.setExtentsFromToken(v2, self) }
    ;

graphTerm returns [expr]
    :   expr=iriRef
    |   expr=rdfLiteral
    |   (   MINUS expr=numericLiteral
            { expr = nodes.NotSupported() }
        |   ( PLUS )? expr=numericLiteral
        )
    |   expr=booleanLiteral
    |   expr=blankNode
    |   NIL
        { expr = nodes.NotSupported() }
    ;

expression returns [expr]
    :   expr=conditionalOrExpression
    ;

conditionalOrExpression returns [expr]
    :   expr=conditionalAndExpression
        (   OP_OR expr2=conditionalAndExpression
            { expr = nodes.Or(expr, expr2) }
        )*
    ;

conditionalAndExpression returns [expr]
    :   expr=valueLogical
        (   OP_AND expr2=valueLogical
            { expr = nodes.And(expr, expr2) }
        )*
    ;

valueLogical returns [expr]
    :   expr=relationalExpression
    ;

relationalExpression returns [expr]
    :   expr=numericExpression
        (   OP_EQ expr2=numericExpression
            { expr = nodes.Equal(expr, expr2) }
        |   OP_NE expr2=numericExpression
            { expr = nodes.Different(expr, expr2) }
        |   OP_LT expr2=numericExpression
            { expr = nodes.LessThan(expr, expr2) }
        |   OP_GT expr2=numericExpression
            { expr = nodes.GreaterThan(expr, expr2) }
        |   OP_LE expr2=numericExpression
            { expr = nodes.LessThanOrEqual(expr, expr2) }
        |   OP_GE expr2=numericExpression
            { expr = nodes.GreaterThanOrEqual(expr, expr2) }
        )?
    ;

numericExpression returns [expr]
    :   expr=additiveExpression
    ;

additiveExpression returns [expr]
    :   expr=multiplicativeExpression
        (   PLUS mult=multiplicativeExpression
            { expr = nodes.NotSupported(); }
        |   MINUS mult=multiplicativeExpression
            { expr = nodes.NotSupported(); }
        )*
    ;

multiplicativeExpression returns [expr]
    :   expr=unaryExpression
        (   TIMES unary=unaryExpression
            { expr = nodes.NotSupported(); }
        |   DIV unary=unaryExpression
            { expr = nodes.NotSupported(); }
        )*
    ;

unaryExpression returns [expr]
    :   OP_NOT prim=primaryExpression
        { expr = nodes.NotSupported(); }
    |   PLUS prim=primaryExpression
        { expr = nodes.NotSupported(); }
    |   MINUS prim=primaryExpression
        { expr = nodes.NotSupported(); }
    |   expr=primaryExpression
    ;

primaryExpression returns [expr]
    :   expr=brackettedExpression
    |   expr=builtInCall
    |   expr=iriRefOrFunction
    |   expr=rdfLiteral
    |   expr=numericLiteral
    |   expr=booleanLiteral
    |   expr=blankNode
    |   expr=var
    ;

brackettedExpression returns [expr]
    :   LPAREN expr=expression RPAREN
    ;

builtInCall returns [expr]
    :   STR LPAREN param=expression RPAREN
        { expr = nodes.NotSupported(); }
    |   LANG LPAREN param=expression RPAREN
        { expr = nodes.NotSupported(); }
    |   LANGMATCHES LPAREN param1=expression COMMA param2=expression RPAREN
        { expr = nodes.NotSupported(); }
    |   DATATYPE LPAREN param=expression RPAREN
        { expr = nodes.NotSupported(); }
    |   BOUND LPAREN param=var RPAREN
        { expr = nodes.NotSupported(); }
    |   IS_IRI LPAREN param=expression RPAREN
        { expr = nodes.NotSupported(); }
    |   IS_URI LPAREN param=expression RPAREN
        { expr = nodes.NotSupported(); }
    |   IS_BLANK LPAREN param=expression RPAREN
        { expr = nodes.NotSupported(); }
    |   IS_LITERAL LPAREN param=expression RPAREN
        { expr = nodes.NotSupported(); }
    |   expr=regexExpression
    ;

regexExpression returns [expr]
    :   REGEX LPAREN expr1=expression
        COMMA expr2=expression
        ( COMMA expr3=expression )? RPAREN
        { expr = nodes.NotSupported(); }
    ;

iriRefOrFunction returns [expr]
    :   expr=iriRef
        (   { expr = nodes.FunctionCall(expr) }
            argList[expr]
        )?
    ;

rdfLiteral returns [expr]
    :   expr=string
        (   lt:LANGTAG
            { expr.literal.lang = lt.getText() }
        |   ( DCARET uriNode=iriRef )
            { expr.literal.typeUri = uriNode.uri }
        )?
    ;

numericLiteral returns [expr]
    :   i:INTEGER
        { expr = self.makeTypedLiteral(i.getText(), xsd.integer); \
          expr.setExtentsFromToken(i, self)}
    |   de:DECIMAL
        { expr = self.makeTypedLiteral(de.getText(), xsd.decimal); \
          expr.setExtentsFromToken(de, self)}
    |   db:DOUBLE
        { expr = self.makeTypedLiteral(db.getText(), xsd.double); \
          expr.setExtentsFromToken(db, self)}
    ;

booleanLiteral returns [expr]
    :   t:TRUE
        { expr = self.makeTypedLiteral("true", xsd.boolean); \
          expr.setExtentsFromToken(t, self)}
    |   f:FALSE
        { expr = self.makeTypedLiteral("false", xsd.boolean); \
          expr.setExtentsFromToken(f, self)}
    ;

string returns [expr]
    :   s1:STRING_LITERAL1
        { expr = nodes.Literal(s1.getText()); \
          expr.setExtentsFromToken(s1, self) }
    |   s2:STRING_LITERAL2
        { expr = nodes.Literal(s2.getText()); \
          expr.setExtentsFromToken(s2, self) }
    |   s1l:STRING_LITERAL_LONG1
        { expr = nodes.Literal(s1l.getText()); \
          expr.setExtentsFromToken(s1l, self) }
    |   s2l:STRING_LITERAL_LONG2
        { expr = nodes.Literal(s2l.getText()); \
          expr.setExtentsFromToken(s2l, self) }
    ;

iriRef returns [expr]
    :   iri:Q_IRI_REF
        { expr = nodes.Uri(iri.getText()); \
          expr.setExtentsFromToken(iri, self) }
    |   expr=qname
    ;

qname returns [expr]
    :   qn:QNAME
        { expr = self.resolveQName(qn) }
    ;

blankNode returns [expr]
    :   bnl:BLANK_NODE_LABEL
        { expr = nodes.NotSupported(); \
          expr.setExtentsFromToken(bnl, self) }
    |   an:ANON
        { expr = nodes.NotSupported(); \
          expr.setExtentsFromToken(an, self) }
    ;


/*----------------------------------------------------------------------
 * Lexical Analyzer
 *--------------------------------------------------------------------*/

class SparqlLexer extends Lexer;

options {
    k = 4;
    charVocabulary = '\u0000'..'\uFFFE';
    caseSensitiveLiterals = false;
}


/*
 * Whitespace and comments
 */

WS
    :   ( ' '
        | '\t'
        | '\n' { $newline }
        | '\r' { $newline }
        )
        { $skip }
    ;


/*
 * Symbols and operators
 */

protected  /* See INTEGER_OR_DECIMAL_OR_DOUBLE_OR_DOT. */
DOT
    :   '.'
    ;

OP_NOT
    :   '!'
    ;

OP_OR
    :   "||"
    ;

OP_AND
    :   "&&"
    ;

TIMES
    :   '*'
    ;

PLUS
    :   '+'
    ;

MINUS
    :   '-'
    ;

DIV
    :   '/'
    ;

COMMA
    :   ','
    ;

SEMICOLON
    :   ';'
    ;

OP_EQ
    :   '='
    ;

OP_NE
    :   "!="
    ;

protected  /* See OP_OR_Q_IRI_REF. */
OP_LT
    :   '<'
    ;

protected  /* See OP_OR_Q_IRI_REF. */
OP_LE
    :   "<="
    ;

OP_GT
    :   '>'
    ;

OP_GE
    :   ">="
    ;

DCARET
    :   "^^"
    ;

protected  /* See LPAREN_OR_NIL. */
LPAREN
    :   '('
    ;

RPAREN
    :   ')'
    ;

protected  /* See LBRACKET_OR_ANON. */
LBRACKET
    :   '['
    ;

RBRACKET
    :   ']'
    ;

LBRACE
    :   '{'
    ;

RBRACE
    :   '}'
    ;



/*
 * Qnames and Keywords
 */

protected  /* See QNAME_OR_KEYWORD. */
QNAME
    :   ( NCNAME_PREFIX )? ':' ( NCNAME )?
    ;

protected  /* See QNAME_OR_KEYWORD. */
ASC
    :   ('A'|'a') ('S'|'s') ('C'|'c')
    ;

protected  /* See QNAME_OR_KEYWORD. */
ASK
    :   ('A'|'a') ('S'|'s') ('K'|'k')
    ;

protected  /* See QNAME_OR_KEYWORD. */
BASE
    :   ('B'|'b') ('A'|'a') ('S'|'s') ('E'|'e')
    ;

protected  /* See QNAME_OR_KEYWORD. */
BOUND
    :   ('B'|'b') ('O'|'o') ('U'|'u') ('N'|'n') ('D'|'d')
    ;

protected  /* See QNAME_OR_KEYWORD. */
BY
    :   ('B'|'b') ('Y'|'y')
    ;

protected  /* See QNAME_OR_KEYWORD. */
CONSTRUCT
    :   ('C'|'c') ('O'|'o') ('N'|'n') ('S'|'s') ('T'|'t') ('R'|'r')
        ('U'|'u') ('C'|'c') ('T'|'t')
    ;

protected  /* See QNAME_OR_KEYWORD. */
DATATYPE
    :   ('D'|'d') ('A'|'a') ('T'|'t') ('A'|'a') ('T'|'t') ('Y'|'y')
        ('P'|'p') ('E'|'e')
    ;

protected  /* See QNAME_OR_KEYWORD. */
DESC
    :   ('D'|'d') ('E'|'e') ('S'|'s') ('C'|'c')
    ;

protected  /* See QNAME_OR_KEYWORD. */
DESCRIBE
    :   ('D'|'d') ('E'|'e') ('S'|'s') ('C'|'c') ('R'|'r') ('I'|'i')
        ('B'|'b') ('E'|'e')
    ;

protected  /* See QNAME_OR_KEYWORD. */
DISTINCT
    :   ('D'|'d') ('I'|'i') ('S'|'s') ('T'|'t') ('I'|'i') ('N'|'n')
        ('C'|'c') ('T'|'t')
    ;

protected  /* See QNAME_OR_KEYWORD. */
FILTER
    :   ('F'|'f') ('I'|'i') ('L'|'l') ('T'|'t') ('E'|'e') ('R'|'r')
    ;

protected  /* See QNAME_OR_KEYWORD. */
FROM
    :   ('F'|'f') ('R'|'r') ('O'|'o') ('M'|'m')
    ;

protected  /* See QNAME_OR_KEYWORD. */
GRAPH
    :   ('G'|'g') ('R'|'r') ('A'|'a') ('P'|'p') ('H'|'h')
    ;

protected  /* See QNAME_OR_KEYWORD. */
LANG
    :   ('L'|'l') ('A'|'a') ('N'|'n') ('G'|'g')
    ;

protected  /* See QNAME_OR_KEYWORD. */
LANGMATCHES
    :   ('L'|'l') ('A'|'a') ('N'|'n') ('G'|'g') ('M'|'m') ('A'|'a')
        ('T'|'t') ('C'|'c') ('H'|'h') ('E'|'e') ('S'|'s')
    ;

protected  /* See QNAME_OR_KEYWORD. */
LIMIT
    :   ('L'|'l') ('I'|'i') ('M'|'m') ('I'|'i') ('T'|'t')
    ;

protected  /* See QNAME_OR_KEYWORD. */
NAMED
    :   ('N'|'n') ('A'|'a') ('M'|'m') ('E'|'e') ('D'|'d')
    ;

protected  /* See QNAME_OR_KEYWORD. */
OFFSET
    :   ('O'|'o') ('F'|'f') ('F'|'f') ('S'|'s') ('E'|'e') ('T'|'t')
    ;

protected  /* See QNAME_OR_KEYWORD. */
OPTIONAL
    :   ('O'|'o') ('P'|'p') ('T'|'t') ('I'|'i') ('O'|'o') ('N'|'n')
        ('A'|'a') ('L'|'l')
    ;

protected  /* See QNAME_OR_KEYWORD. */
ORDER
    :   ('O'|'o') ('R'|'r') ('D'|'d') ('E'|'e') ('R'|'r')
    ;

protected  /* See QNAME_OR_KEYWORD. */
PREFIX
    :   ('P'|'p') ('R'|'r') ('E'|'e') ('F'|'f') ('I'|'i') ('X'|'x')
    ;

protected  /* See QNAME_OR_KEYWORD. */
REGEX
    :   ('R'|'r') ('E'|'e') ('G'|'g') ('E'|'e') ('X'|'x')
    ;

protected  /* See QNAME_OR_KEYWORD. */
SELECT
    :   ('S'|'s') ('E'|'e') ('L'|'l') ('E'|'e') ('C'|'c') ('T'|'t')
    ;

protected  /* See QNAME_OR_KEYWORD. */
STR
    :   ('S'|'s') ('T'|'t') ('R'|'r')
    ;

protected  /* See QNAME_OR_KEYWORD. */
UNION
    :   ('U'|'u') ('N'|'n') ('I'|'i') ('O'|'o') ('N'|'n')
    ;

protected  /* See QNAME_OR_KEYWORD. */
WHERE
    :   ('W'|'w') ('H'|'h') ('E'|'e') ('R'|'r') ('E'|'e')
    ;

protected  /* See QNAME_OR_KEYWORD. */
RDF_TYPE_ABBREV
    :   "a"
    ;

protected  /* See QNAME_OR_KEYWORD. */
TRUE
    :   "true"
    ;

protected  /* See QNAME_OR_KEYWORD. */
FALSE
    :   "false"
    ;

protected  /* See QNAME_OR_KEYWORD. */
IS_BLANK
    :   "isBLANK"
    ;

protected  /* See QNAME_OR_KEYWORD. */
IS_IRI
    :   "isIRI"
    ;

protected  /* See QNAME_OR_KEYWORD. */
IS_LITERAL
    :   "isLITERAL"
    ;

protected  /* See QNAME_OR_KEYWORD. */
IS_URI
    :   "isURI"
    ;


QNAME_OR_KEYWORD
    :   ( QNAME ) => QNAME
        { $setType(QNAME) }
    |   ( ASC ) => ASC
        { $setType(ASC) }
    |   ( ASK ) => ASK
        { $setType(ASK) }
    |   ( BASE ) => BASE
        { $setType(BASE) }
    |   ( BOUND ) => BOUND
        { $setType(BOUND) }
    |   ( BY ) => BY
        { $setType(BY) }
    |   ( CONSTRUCT ) => CONSTRUCT
        { $setType(CONSTRUCT) }
    |   ( DATATYPE ) => DATATYPE
        { $setType(DATATYPE) }
    |   ( DESCRIBE ) => DESCRIBE
        { $setType(DESCRIBE) }
    |   ( DESC ) => DESC
        { $setType(DESC) }
    |   ( DISTINCT ) => DISTINCT
        { $setType(DISTINCT) }
    |   ( FILTER ) => FILTER
        { $setType(FILTER) }
    |   ( FROM ) => FROM
        { $setType(FROM) }
    |   ( GRAPH ) => GRAPH
        { $setType(GRAPH) }
    |   ( LANGMATCHES ) => LANGMATCHES
        { $setType(LANGMATCHES) }
    |   ( LANG ) => LANG
        { $setType(LANG) }
    |   ( LIMIT ) => LIMIT
        { $setType(LIMIT) }
    |   ( NAMED ) => NAMED
        { $setType(NAMED) }
    |   ( OFFSET ) => OFFSET
        { $setType(OFFSET) }
    |   ( OPTIONAL ) => OPTIONAL
        { $setType(OPTIONAL) }
    |   ( ORDER ) => ORDER
        { $setType(ORDER) }
    |   ( PREFIX ) => PREFIX
        { $setType(PREFIX) }
    |   ( REGEX ) => REGEX
        { $setType(REGEX) }
    |   ( SELECT ) => SELECT
        { $setType(SELECT) }
    |   ( STR ) => STR
        { $setType(STR) }
    |   ( UNION ) => UNION
        { $setType(UNION) }
    |   ( WHERE ) => WHERE
        { $setType(WHERE) }
    |   ( RDF_TYPE_ABBREV ) => RDF_TYPE_ABBREV
        { $setType(RDF_TYPE_ABBREV) }
    |   ( TRUE ) => TRUE
        { $setType(TRUE) }
    |   ( FALSE ) => FALSE
        { $setType(FALSE) }
    |   ( IS_BLANK ) => IS_BLANK
        { $setType(IS_BLANK) }
    |   ( IS_IRI ) => IS_IRI
        { $setType(IS_IRI) }
    |   ( IS_LITERAL ) => IS_LITERAL
        { $setType(IS_LITERAL) }
    |   ( IS_URI ) => IS_URI
        { $setType(IS_URI) }
    ;


/*
 * IRI references and blank node IDs
 */

protected  /* See OP_LT_OR_Q_IRI_REF. */
Q_IRI_REF
    :   '<'!
        (
            ~( '<' | '>' | '\'' | '{' | '}' | '|' | '^' | '`' |
               '\u0000'..'\u0020'
            )
        )*
        '>'!
    ;

OP_OR_Q_IRI_REF
    :   ( Q_IRI_REF ) => Q_IRI_REF
        { $setType(Q_IRI_REF) }
    |   ( OP_LE ) => OP_LE
        { $setType(OP_LE) }
    |   ( OP_LT ) => OP_LT
        { $setType(OP_LT) }
    ;

LANGTAG
    :   '@' ('a'..'z' | 'A'..'Z')+ ('-' ('a'..'z' | 'A'..'Z' | DIGIT)+)*
    ;


BLANK_NODE_LABEL
    :   '_' ':' NCNAME
    ;


/*
 * Variables
 */

VAR1
    :   '?'! VARNAME
    ;

VAR2
    :   '$'! VARNAME
    ;


/*
 * Numbers
 */

protected  /* See INTEGER_OR_DECIMAL_OR_DOUBLE_OR_DOT. */
INTEGER
    :   (DIGIT)+
    ;

protected  /* See INTEGER_OR_DECIMAL_OR_DOUBLE_OR_DOT. */
DECIMAL
    :   (DIGIT)+ '.' (DIGIT)*
    |   '.' (DIGIT)+
    ;

protected  /* See INTEGER_OR_DECIMAL_OR_DOUBLE_OR_DOT. */
DOUBLE
    :   ( DIGIT )+
        ( '.' ( DIGIT )* )?
        EXPONENT
    |   '.' ((DIGIT))+ EXPONENT
    ;

protected
EXPONENT
    :   ('e' | 'E') ('+' | '-')? (DIGIT)+
    ;

protected
DIGIT
    :   '0'..'9'
    ;

INTEGER_OR_DECIMAL_OR_DOUBLE_OR_DOT
    :   ( DOUBLE ) => DOUBLE
        { $setType(DOUBLE) }
    |   ( DECIMAL ) => DECIMAL
        { $setType(DECIMAL) }
    |   ( INTEGER ) => INTEGER
        { $setType(INTEGER) }
    |   ( DOT ) => DOT
        { $setType(DOT) }
    ;


/*
 * Nil and Anon
 */

protected  /* See LPAREN_OR_NIL. */
NIL
    :   '(' ( WS )* ')'
    ;

LPAREN_OR_NIL
    :   ( NIL ) => NIL
        { $setType(NIL) }
    |   ( LPAREN ) => LPAREN
        { $setType(LPAREN) }
    ;

protected  /* See LBRACKET_OR_ANON. */
ANON
    :   '[' ( WS )* ']'
    ;

LBRACKET_OR_ANON
    :   ( ANON ) => ANON
        { $setType(ANON) }
    |   ( LBRACKET ) => LBRACKET
        { $setType(LBRACKET) }
    ;


/*
 * Strings Literals
 */

protected
STRING_LITERAL1  /* See STRING_LITERAL1_OR_LONG. */
    :   '\''!
        ( ~('\u0027' | '\u005C' | '\u000A' | '\u000D')
        | ECHAR
        | UCHAR
        )*
        '\''!
    ;

protected
STRING_LITERAL2  /* See STRING_LITERAL2_OR_LONG. */
    :   '"'!
        (   ~( '\u0022' | '\u005C' | '\u000A' | '\u000D' )
        |   ECHAR
        |   UCHAR
        )* '"'!
    ;

protected
LONG_STRING_CHAR
    :   ~( '\'' | '"' | '\\' )
    |   ECHAR
    |   UCHAR
    ;

protected
STRING_LITERAL_LONG1  /* See STRING_LITERAL1_OR_LONG. */
    :   "'''"!
        (   '\'' ( LONG_STRING_CHAR | '"' )
        |   '\'' '\'' ( LONG_STRING_CHAR | '"' )
        |   ( LONG_STRING_CHAR | '"' )
        )*
        "'''"!
    ;

protected
STRING_LITERAL_LONG2  /* See STRING_LITERAL2_OR_LONG. */
    :   '"'! '"'! '"'!
        (   '"' ( LONG_STRING_CHAR | '\'' )
        |   '"' '"' ( LONG_STRING_CHAR | '\'' )
        |   ( LONG_STRING_CHAR | '\'' )
        )*
        '"'! '"'! '"'!
    ;

STRING_LITERAL1_OR_LONG
    :   ( "'''" ) => STRING_LITERAL_LONG1
        { $setType(STRING_LITERAL_LONG1) }
    |   ( "'" ) => STRING_LITERAL1
        { $setType(STRING_LITERAL1) }
    ;

STRING_LITERAL2_OR_LONG
    :   ( '"' '"' '"' ) => STRING_LITERAL_LONG2
        { $setType(STRING_LITERAL_LONG2) }
    |   ( '"' ) => STRING_LITERAL2
        { $setType(STRING_LITERAL2) }
    ;

protected
ECHAR
    :   '\\'!
        (   't'
            { $setText("\t") }
        |   'b'
            { $setText("\b") }
        |   'n'
            { $setText("\n") }
        |   'r'
            { $setText("\r") }
        |   'f'
            { $setText("\f") }
        |   '"'
        |   '\\'
        |   '\''
        )
    ;

protected
UCHAR
    :   '\\'!
        (   'u'! HEX HEX HEX HEX
            {
                text = unichr(int($getText, 16));
                $setText(text)
            }
        |   'U'! HEX HEX HEX HEX HEX HEX HEX HEX
            {
                text = unichr(int($getText, 16));
                $setText(text)
            }
        )
    ;

protected
HEX
    :   DIGIT
    |   'A'..'F'
    |   'a'..'f'
    ;

protected
NCCHAR1p
    :   'A'..'Z'
    |   'a'..'z'
    |   '\u00C0'..'\u00D6'
    |   '\u00D8'..'\u00F6'
    |   '\u00F8'..'\u02FF'
    |   '\u0370'..'\u037D'
    |   '\u037F'..'\u1FFF'
    |   '\u200C'..'\u200D'
    |   '\u2070'..'\u218F'
    |   '\u2C00'..'\u2FEF'
    |   '\u3001'..'\uD7FF'
    |   '\uF900'..'\uFDCF'
    |   '\uFDF0'..'\uFFFD'
/*    |   '\u10000'..'\uEFFFF'*/
    |   UCHAR
    ;

protected
NCCHAR1
    :   NCCHAR1p | '_'
    ;

protected
VARNAME
    :   (   NCCHAR1
        |   DIGIT
        )
        (   NCCHAR1
        |   DIGIT
        |   '\u00B7'
        |   '\u0300'..'\u036F'
        |   '\u203F'..'\u2040'
        )*
    ;

protected
NCCHAR
    :   NCCHAR1
    |   '-'
    |   DIGIT
    |   '\u00B7'
    |   '\u0300'..'\u036F'
    |   '\u203F'..'\u2040'
    ;

protected
NCNAME_PREFIX
    :   NCCHAR1p
        (   NCCHAR
        |   '.' NCCHAR
        )*
    ;

protected
NCNAME
    :   NCCHAR1
        (   NCCHAR
        |   '.' NCCHAR
        )*
    ;
