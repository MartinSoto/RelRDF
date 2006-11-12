header {
    from relrdf.commonns import rdf, xsd
    from relrdf.expression import nodes

    import parser
    import sqlnodes
}

options {
    language = "Python";
}

/*----------------------------------------------------------------------
 * Parser
 *--------------------------------------------------------------------*/

class ExpressionParser extends Parser("parser.Parser");

options {
    defaultErrorHandler=false;
}


expression returns [expr]
    :   expr=mapTableExpression
    ;

mapTableExpression returns [expr]
    :   expr=selectTableExpression
    |   m:"map" expr=mapTableExpression "to" rp:LPAREN
        specs=mapList RPAREN
        { expr = nodes.MapResult(specs[1], expr, *specs[0]); \
          expr.setExtentsStartFromToken(m, self); \
          expr.setExtentsEndFromToken(rp) }
    ;

mapList returns [specs]
    :   { specs = ([], []) }
        colSpec[specs]
        (   COMMA colSpec[specs] )*
    ;

colSpec[specs]
    :   expr=scalarExpression
        { colName = ""; }
        (   "as" cn:IDENTIFIER
            { colName = cn.getText() }
        )?
        { specs[0].append(expr); \
          specs[1].append(colName); }
    ;

selectTableExpression returns [expr]
    :   expr=productTableExpression
        (   "on" pred=scalarExpression
            { expr = nodes.Select(expr, pred) }
        )?
    ;

productTableExpression returns [expr]
    :   expr=basicTableExpression
        (   "cross" expr2=productTableExpression
            { expr = nodes.Product(expr, expr2) }
        )?
    ;

basicTableExpression returns [expr]
    :   expr=tableRef
    |   LPAREN expr=expression RPAREN
    ;



tableRef returns [expr]
    :   t:IDENTIFIER
        { expr = sqlnodes.SqlRelation(t.getText(), t.getText()); \
          expr.setExtentsFromToken(t, self) }
        (   "as" i:IDENTIFIER
            { expr.incarnation = i.getText(); \
              expr.setExtentsEndFromToken(i) }
        )?
    ;



functionCall returns [expr]
    :   name=iriRef
        { expr = nodes.FunctionCall(name) }
        argList[expr]
        { expr = nodes.NotSupported(expr) }
    ;

argList[funcCall]
    :   (   nil:NIL
            { funcCall.setExtentsEndFromToken(nil) }
        |   LPAREN param=scalarExpression
            { funcCall.append(param) }
            (    COMMA param=scalarExpression
                { funcCall.append(param) }
            )*
            rp:RPAREN
            { funcCall.setExtentsEndFromToken(rp) }
        )
    ;

columnRef returns [expr]
    :   t:IDENTIFIER DOT cn:IDENTIFIER
        { expr = sqlnodes.SqlFieldRef(t.getText(), cn.getText()); \
          expr.setExtentsStartFromToken(t, self); \
          expr.setExtentsEndFromToken(cn) }
    ;

scalarExpression returns [expr]
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
            { expr = nodes.NotSupported(expr, mult); }
        |   MINUS mult=multiplicativeExpression
            { expr = nodes.NotSupported(expr, mult); }
        )*
    ;

multiplicativeExpression returns [expr]
    :   expr=unaryExpression
        (   TIMES unary=unaryExpression
            { expr = nodes.NotSupported(expr, unary); }
        |   DIV unary=unaryExpression
            { expr = nodes.NotSupported(expr, unary); }
        )*
    ;

unaryExpression returns [expr]
    :   on:OP_NOT prim=primaryExpression
        { expr = nodes.NotSupported(prim); \
          expr.setExtentsStartFromToken(on, self); }
    |   plus:PLUS prim=primaryExpression
        { expr = nodes.NotSupported(prim); \
          expr.setExtentsStartFromToken(plus, self); }
    |   minus:MINUS prim=primaryExpression
        { expr = nodes.NotSupported(prim); \
          expr.setExtentsStartFromToken(minus, self); }
    |   expr=primaryExpression
    ;

primaryExpression returns [expr]
    :   expr=brackettedExpression
    |   expr=iriRefOrFunction
    |   expr=rdfLiteral
    |   expr=numericLiteral
    |   expr=booleanLiteral
    |   expr=columnRef
    ;

brackettedExpression returns [expr]
    :   LPAREN expr=scalarExpression RPAREN
    ;

regexExpression returns [expr]
    :   rg:REGEX LPAREN expr1=scalarExpression
        COMMA expr2=scalarExpression
        ( COMMA expr3=scalarExpression )? rp:RPAREN
        { expr = nodes.NotSupported(); \
          expr.setExtentsStartFromToken(rg, self); \
          expr.setExtentsEndFromToken(rp); }
    ;

iriRefOrFunction returns [expr]
    :   expr=iriRef
        (   { expr = nodes.FunctionCall(expr) }
            argList[expr]
            { expr = nodes.NotSupported(expr) }
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
    :   t:"true"
        { expr = self.makeTypedLiteral("true", xsd.boolean); \
          expr.setExtentsFromToken(t, self)}
    |   f:"false"
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


/*----------------------------------------------------------------------
 * Lexical Analyzer
 *--------------------------------------------------------------------*/

class ExpressionLexer extends Lexer;

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
 * Qnames and Identifiers
 */

protected  /* See QNAME_OR_KEYWORD. */
QNAME
    :   ( NCNAME_PREFIX )? ':' ( NCNAME )?
    ;

protected
IDENTIFIER
    :   NCCHAR1
        (   NCCHAR1
        |   DIGIT
        |   '\u00B7'
        |   '\u0300'..'\u036F'
        |   '\u203F'..'\u2040'
        )*
    ;

QNAME_OR_IDENTIFIER
    :   ( QNAME ) => QNAME
        { $setType(QNAME) }
    |   ( IDENTIFIER ) => IDENTIFIER
        { $setType(IDENTIFIER) }
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

