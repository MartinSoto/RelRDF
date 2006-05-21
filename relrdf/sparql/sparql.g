header {
    from relrdf.expression import nodes

    import parser
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

query
    :   prolog
        (   selectQuery
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
    :   PREFIX QNAME Q_IRI_REF
        /* FIXME: Check for QNAME_NS */
    ;

selectQuery
    :   SELECT
        ( DISTINCT )?
        ( ( var )+ | TIMES )
        ( datasetClause )*
        whereClause
        solutionModifier
    ;

constructQuery
    :   CONSTRUCT
        constructTemplate
        ( datasetClause )*
        whereClause
        solutionModifier
    ;

describeQuery
    :   DESCRIBE
        ( ( varOrIriRef )+ | TIMES )
        ( datasetClause )*
        ( whereClause )?
        solutionModifier
    ;

askQuery
    :   ASK
        ( datasetClause )*
        whereClause
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
    :   NAMED
        sourceSelector
    ;

sourceSelector
    :   iriRef
    ;

whereClause
    :   ( WHERE )?
        groupGraphPattern
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

groupGraphPattern
    :   LBRACE graphPattern RBRACE
    ;

graphPattern
    :   filteredBasicGraphPattern
        (   graphPatternNotTriples
            ( DOT )?
            graphPattern
        )?
    ;

filteredBasicGraphPattern
    :   ( blockOfTriples )?
        (   constraint
            ( DOT )?
            filteredBasicGraphPattern
        )?
    ;

blockOfTriples
    :   triplesSameSubject ( DOT ( triplesSameSubject )? )*
    ;

graphPatternNotTriples
    :   optionalGraphPattern | groupOrUnionGraphPattern | graphGraphPattern
    ;

optionalGraphPattern
    :   OPTIONAL groupGraphPattern
    ;

graphGraphPattern
    :   GRAPH varOrBlankNodeOrIriRef groupGraphPattern
    ;

groupOrUnionGraphPattern
    :   groupGraphPattern ( UNION groupGraphPattern )*
    ;

constraint
    :   FILTER ( brackettedExpression | builtInCall | functionCall )
    ;

functionCall
    :   iriRef argList
    ;

argList
    :   ( NIL | LPAREN expression ( COMMA expression )* RPAREN )
    ;

constructTemplate
    :   LBRACE constructTriples RBRACE
    ;

constructTriples
    :   ( triplesSameSubject ( DOT constructTriples )? )?
    ;

triplesSameSubject
    :   varOrTerm propertyListNotEmpty | triplesNode propertyList
    ;

propertyList
    :   ( propertyListNotEmpty )?
    ;

propertyListNotEmpty
    :   verb objectList ( SEMICOLON propertyList )?
    ;

objectList
    :   graphNode ( COMMA objectList )?
    ;

verb
    :   varOrIriRef | RDF_TYPE_ABBREV
    ;

triplesNode
    :   collection | blankNodePropertyList
    ;

blankNodePropertyList
    :   LBRACKET propertyListNotEmpty RBRACKET
    ;

collection
    :   LPAREN ( graphNode )+ RPAREN
    ;

graphNode
    :   varOrTerm | triplesNode
    ;

varOrTerm
    :   var | graphTerm
    ;

varOrIriRef
    :   var | iriRef
    ;

varOrBlankNodeOrIriRef
    :   var | blankNode | iriRef
    ;

var
    :   VAR1 | VAR2
    ;

graphTerm
    :   iriRef | rdfLiteral
    |   ( MINUS | PLUS )? numericLiteral
    |   booleanLiteral
    |   blankNode
    |   NIL
    ;

expression
    :   conditionalOrExpression
    ;

conditionalOrExpression
    :   conditionalAndExpression
        (   OP_OR
            conditionalAndExpression
        )*
    ;

conditionalAndExpression
    :   valueLogical ( OP_AND valueLogical )*
    ;

valueLogical
    :   relationalExpression
    ;

relationalExpression
    :   numericExpression
        (   OP_EQ numericExpression
        |   OP_NE numericExpression
        |   OP_LT numericExpression
        |   OP_GT numericExpression
        |   OP_LE numericExpression
        |   OP_GE numericExpression
        )?
    ;

numericExpression
    :   additiveExpression
    ;

additiveExpression
    :   multiplicativeExpression
        (   PLUS multiplicativeExpression
        |   MINUS multiplicativeExpression
        )*
    ;

multiplicativeExpression
    :   unaryExpression
        (   TIMES unaryExpression
        |   DIV unaryExpression
        )*
    ;

unaryExpression
    :   OP_NOT primaryExpression
    |   PLUS primaryExpression
    |   MINUS primaryExpression
    |   primaryExpression
    ;

primaryExpression
    :   brackettedExpression
    |   builtInCall
    |   iriRefOrFunction
    |   rdfLiteral
    |   numericLiteral
    |   booleanLiteral
    |   blankNode
    |   var
    ;

brackettedExpression
    :   LPAREN expression RPAREN
    ;

builtInCall
    :   STR LPAREN expression RPAREN
    |   LANG LPAREN expression RPAREN
    |   LANGMATCHES LPAREN expression COMMA expression RPAREN
    |   DATATYPE LPAREN expression RPAREN
    |   BOUND LPAREN var RPAREN
    |   IS_IRI LPAREN expression RPAREN
    |   IS_URI LPAREN expression RPAREN
    |   IS_BLANK LPAREN expression RPAREN
    |   IS_LITERAL LPAREN expression RPAREN
    |   regexExpression
    ;

regexExpression
    :   REGEX LPAREN expression COMMA expression ( COMMA expression )? RPAREN
    ;

iriRefOrFunction
    :   iriRef ( argList )?
    ;

rdfLiteral
    :   string ( LANGTAG | ( DCARET iriRef ) )?
    ;

numericLiteral
    :   INTEGER | DECIMAL | DOUBLE
    ;

booleanLiteral
    :   TRUE | FALSE
    ;

string
    :   STRING_LITERAL1
    |   STRING_LITERAL2
    |   STRING_LITERAL_LONG1
    |   STRING_LITERAL_LONG2
    ;

iriRef
    :   Q_IRI_REF | qname
    ;

qname
    :   QNAME | QNAME_NS
    ;

blankNode
    :   BLANK_NODE_LABEL | ANON
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
    :   (   ' '
        |   '\t'
        |   '\r'
        |   '\n'
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
    :   '\''
        ( ~('\u0027' | '\u005C' | '\u000A' | '\u000D')
        | ECHAR
        | UCHAR
        )*
        '\''
    ;

protected
STRING_LITERAL2  /* See STRING_LITERAL2_OR_LONG. */
    :   '"'
        (   ~( '\u0022' | '\u005C' | '\u000A' | '\u000D' )
        |   ECHAR
        |   UCHAR
        )* '"'
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

