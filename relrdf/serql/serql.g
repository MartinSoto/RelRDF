header {
    from relrdf.expression import nodes

    import parser
}

options {
    language="Python";
}

/*----------------------------------------------------------------------
 * Parser
 *--------------------------------------------------------------------*/

class SerQLParser extends Parser("parser.Parser");

options {
    defaultErrorHandler=false;
}


query returns [expr]
    :   expr=querySet ( namespaceList )?
        { expr = self.expandQNames(expr) }
    ;

namespaceList
    :   "using" "namespace" namespace ( "," namespace )*
    ;

namespace
    :   prefix=prefixName "=" fu:FULL_URI
        { self.createLocalPrefix(prefix, fu.getText()) }
    ;

/* This rule should use PREFIX_NAME instead of NC_NAME, but this leads
to ambiguities. Since the only difference is that a NC_NAME can be a
single underscore, we check for this case explicitly. */
prefixName returns [prefix]
    :   nn:NC_NAME
        { prefix = self.checkPrefix(nn) }
    ;


querySet returns [expr]
    :   expr = simpleQuery
        (   factory=setOperator expr2=querySet
            { return self.setOperationExpr(factory, expr, expr2) }
        )?
    ;

simpleQuery returns [expr]
    :   "(" expr=querySet ")"
    |   expr=selectQuery
    |   expr=constructQuery
    ;

setOperator returns [factory]
    :   "union"
        { factory = nodes.Union }
    |   "minus"
        { factory = nodes.SetDifference }
    |   "intersect"
        { factory = nodes.Intersection }
    ;


selectQuery returns [expr]
        { self.pushContext(); \
          condExpr = None }
    :   select:"select" nameBindings=projection
        patternExpr=fromClauseList
        { endSubexpr = patternExpr }
        (   "where" condExpr=booleanExpr
            { endSubexpr = condExpr }
        )?
        { expr = self.selectQueryExpr(nameBindings, patternExpr,
                                      condExpr); \
          expr.setExtentsStartFromToken(select, self); \
          expr.setEndSubexpr(endSubexpr); \
          self.popContext() }
    ;

projection returns [nameBindings]
    :   nameBinding=projectionElem
        { columnNames = [nameBinding[0]]; \
          mappingExprs = [nameBinding[1]] }
        (   "," nameBinding=projectionElem
            { columnNames.append(nameBinding[0]); \
              mappingExprs.append(nameBinding[1]) }
        )*
        { nameBindings = columnNames, mappingExprs }
    ;

projectionElem returns [nameBinding]
    :   mappingExpr=var
        { columnName=mappingExpr.name }
        (   "as" str:STRING
            { columnName = str.getText() }
        )?
        { nameBinding = columnName, mappingExpr }
    |   mappingExpr=value "as" str2:STRING
        { nameBinding = str2.getText(), mappingExpr }
    ;


constructQuery returns [expr]
        { self.pushContext(); \
          condExpr = None }
    :   construct:"construct" resultExpr=constructClause
        patternExpr=fromClauseList
        { endSubexpr = patternExpr }
        (   "where" condExpr=booleanExpr
            { endSubexpr = condExpr }
        )?
        { expr = self.constructQueryExpr(resultExpr, patternExpr,
                                         condExpr); \
          expr.setExtentsStartFromToken(construct, self); \
          expr.setEndSubexpr(endSubexpr); \
          self.popContext() }
    ;

constructClause returns [expr]
    :   "*"
        { expr = None }
    |   expr=pathExprList[nodes.Joker()]
    ;


fromClauseList returns [expr]
    :   expr=fromClause
        (   expr2=fromClause
            { expr=nodes.Product(expr, expr2) }
        )*
    ;

fromClause returns [expr]
    :   "from"
        (
            (   "context"
                (   context=var
                |   context=uri
                |   context=bnode
                |   context=literal
                )
                expr=graphPattern[context]
            )
        |   expr=graphPattern[nodes.Joker()]
        )
    ;

graphPattern [context] returns [expr]
    :   expr=pathExprList[context]
    ;

pathExprList [context] returns [expr]
    :
        expr=pathExpr[context]
        (   "," expr2=pathExpr[context]
            { expr = nodes.Product(expr, expr2) }
        )*
    ;

pathExpr [context] returns [expr]
    :   n1=node[context] e=edge n2=node[context]
        { expr = self.exprFromPattern(context, n1, e, n2) }
        (   expr2=pathExprTail[context, n2]
            { expr = nodes.Product(expr, expr2) }
        |   ";" expr2=pathExprTail[context, n1]
            { expr = nodes.Product(expr, expr2) }
        )?
    ;

pathExprTail [context, n1] returns [expr]
    :   e=edge n2=node[context]
        { expr = self.exprFromPattern(context, n1, e, n2) }
        (   expr2=pathExprTail[context, n2]
            { expr = nodes.Product(expr, expr2) }
        |   ";" expr2=pathExprTail[context, n1]
            { expr = nodes.Product(expr, expr2) }
        )?
    ;

edge returns [expr]
    :   expr=var
    |   expr=uri
    ;

node [context] returns [exprList]
    :   "{"
        { exprList = None }
        (    exprList=nodeElemList[context]
        )?
        { exprList = self.fixNodeList(exprList) }
        "}"
    ;

nodeElemList [context] returns [exprList]
    :   ne1=nodeElem[context]
        { exprList = ne1 }
        (   "," ne=nodeElem[context]
            { exprList.extend(ne) }
        )*
    ;

nodeElem [context] returns [exprList]
    :   expr=var
        { exprList = [expr] }
    |   expr=uri
        { exprList = [expr] }
    |   expr=bnode
        { exprList = [expr] }
    |   expr=literal
        { exprList = [expr] }
    |   exprList=reifiedStat[context]
    ;

reifiedStat [context] returns [exprList]
    :   n1=node[context] e=edge n2=node[context]
        { exprList = self.exprListFromReifPattern(context, n1, e, n2) }
    ;

booleanExpr returns [expr]
    :   expr=andExpr
        (   "or" expr2=booleanExpr
            { expr = nodes.Or(expr, expr2) }
        )?
    ;

andExpr returns [expr]
    :   expr = booleanElem
        (   "and" expr2=andExpr
            { expr = nodes.And(expr, expr2) }
        )?
    ;

booleanElem returns [expr]
    :   lp:"(" expr=booleanExpr rp:")"
        { expr.setExtentsStartFromToken(lp, self); \
          expr.setExtentsEndFromToken(rp) }
    |   notOp:"not" expr1=booleanElem
        { expr = nodes.Not(expr1); \
          expr.setExtentsStartFromToken(notOp, self) }
    |   expr1=varOrValue factory=compOp expr2=varOrValue
        { expr = factory(expr1, expr2) }
    ;

compOp returns [factory]
    :   "="
        { factory = nodes.Equal }
    |   "!="
        { factory = nodes.Different }
    |   "<"
        { factory = nodes.LessThan }
    |   "<="
        { factory = nodes.LessThanOrEqual }
    |   ">"
        { factory = nodes.GreaterThan }
    |   ">="
        { factory = nodes.GreaterThanOrEqual }
    ;

varOrValue returns [expr]
    :   expr=var 
    |   expr=value
    ;

var returns [expr]
    :   nc:NC_NAME
        { expr = nodes.Var(nc.getText()); \
          expr.setExtentsFromToken(nc, self) }
    ;

value returns [expr]
    :   expr=uri
    |   expr=bnode
    |   expr=literal
    ;

uri returns [expr]
    :   uri:FULL_URI
        { expr = nodes.Uri(uri.getText()); \
          expr.setExtentsFromToken(uri, self) }
    |   qn:QNAME
        { expr = nodes.QName(qn.getText()); \
          expr.setExtentsFromToken(qn, self) }
    ;

bnode returns [expr]
    :   bn:BNODE
        { expr = nodes.NotSupported() }
    ;


literal returns [expr]
    :   str:STRING
        { expr = nodes.Literal(str.getText()); \
          expr.setExtentsFromToken(str, self) }
    |   lt:LITERAL
        { expr = nodes.Literal(self.convertLiteral(lt.getText())); \
          expr.setExtentsFromToken(lt, self) }
    |   { sign = 1 }
        (   MINUS
            { sign = -1 }
        |   PLUS
            { sign = 1 }
        )?
        (   i:INTEGER
            { value = sign * int(i.getText()); \
              expr = nodes.Literal(value); \
              expr.setExtentsFromToken(i, self) }
        |   d:DECIMAL
            { value = sign * float(d.getText()); \
              expr = nodes.Literal(value); \
              expr.setExtentsFromToken(d, self) }
        )
    ;


/*----------------------------------------------------------------------
 * Lexical Analyzer
 *--------------------------------------------------------------------*/

class SerQLLexer extends Lexer;

options {
    k=2;
    charVocabulary='\u0000'..'\uFFFE';
    caseSensitiveLiterals=false;
}


/*
 * White space
 */

WS
    :   ( ' '
        | '\t'
        | '\n' ('\r')? { $newline }
        | '\r' ('\n')? { $newline }
        )
        { $skip }
    ;


/*
 * Operators and braces
 */

LE
    :   "<="
    ;

protected /* See LT_OR_URI. */
LT
    :   "<"
    ;

EQ
    :   "="
    ;

GE
    :   ">="
    ;

GT
    :   ">"
    ;

MINUS
    :   "-"
    ;

COMMA
    :   ","
    ;

SEMICOLON
    :   ";"
    ;

COLON
    :   ":"
    ;

NE
    :   "!="
    ;

protected /* See INTEGER_OR_DECIMAL_OR_DOT. */
DOT
    :   "."
    ;

LPAREN
    :   "("
    ;

RPAREN
    :   ")"
    ;

LBRACKET
    :   "["
    ;

RBRACKET
    :   "]"
    ;

LBRACE
    :   "{"
    ;

RBRACE
    :   "}"
    ;

TIMES
    :   "*"
    ;

PLUS
    :   "+"
    ;


/*
 * Symbols
 */


protected /* See QNAME_OR_BNODE_OR_NC_NAME. */
QNAME
    :   PREFIX_NAME ':' (NC_NAME_CHAR)*
    ;

protected /* See QNAME_OR_BNODE_OR_NC_NAME. */
BNODE
    :   "_:" NC_NAME
    ;

protected /* See QNAME_OR_BNODE_OR_NC_NAME. */
NC_NAME
    :   (LETTER | '_') (NC_NAME_CHAR)*
    ;

protected
PREFIX_NAME
    :   LETTER (NC_NAME_CHAR)*
    |   '_' (NC_NAME_CHAR)+
    ;

QNAME_OR_BNODE_OR_NC_NAME
    :   ( PREFIX_NAME ':' ) => QNAME
        { $setType(QNAME) }
    |   ( "_:" ) => BNODE
        { $setType(BNODE) }
    |   NC_NAME
        { $setType(NC_NAME) }
    ;


/*
 * Strings and literals
 */

protected
LITERAL
    :   str:STRING
        (   '@'! lang:LANG
            { $setText("@" + lang.getText() + str.getText()) }
        |   "^^"!
            (   uri:FULL_URI
                { $setText("<" + uri.getText() + ">" + str.getText()) }
            |   qname:QNAME
            )
        )?
    ;

protected
LANG
    :   LANG_ALPHA LANG_ALPHA
    ;

protected
LANG_ALPHA
    :   'A'..'Z' | 'a'..'z'
    ;

protected
STRING
    :   '"'!
        (   STR_CHAR
        |   STR_ESC
        )*
        '"'!
    ;

LITERAL_OR_STRING
    :   ( STRING ( '@' | "^^" ) ) => LITERAL
        { $setType(LITERAL) }
    |   STRING
        { $setType(STRING) }
    ;

protected
STR_CHAR
    :   ~('\\' | '\n' | '"')
    ;

protected
STR_ESC
    /* See http://www.w3.org/TR/rdf-testcases/#ntrip_strings. */
    :   '\\'
        (   
            't'
            { $setText("\t") }
        |   'n'
            { $setText("\n") }
        |   'r'
            { $setText("\r") }
        |   '"'
            { $setText("\"") }
        |   '\\'
            { $setText("\\") }
        |   'u' STR_HEX_DIGIT STR_HEX_DIGIT STR_HEX_DIGIT STR_HEX_DIGIT
            {
                text = unichr(int($getText[2:], 16))
                $setText(text)
            }
        |   'U' STR_HEX_DIGIT STR_HEX_DIGIT STR_HEX_DIGIT STR_HEX_DIGIT
            STR_HEX_DIGIT STR_HEX_DIGIT STR_HEX_DIGIT STR_HEX_DIGIT
            {
                text = unichr(int($getText[2:], 16))
                $setText(text)
            }
        )
    ;

protected
STR_HEX_DIGIT
    :   '0'..'9' | 'A'..'F'
    ;

/*
 * Numbers
 */

protected /* See INTEGER_OR_DECIMAL_OR_DOT. */
INTEGER
    :   (DIGIT)+
    ;

protected /* See INTEGER_OR_DECIMAL_OR_DOT. */
DECIMAL
    :   (DIGIT)* '.' (DIGIT)+
    ;

INTEGER_OR_DECIMAL_OR_DOT
    :   ( (DIGIT)* '.' ) => DECIMAL
        { $setType(DECIMAL) }
    |   ( '.' (DIGIT)+ ) => DECIMAL
        { $setType(DECIMAL) }
    |   INTEGER
        { $setType(INTEGER) }
    |   DOT
        { $setType(DOT) }
    ;

protected
DIGIT
    :   '0'..'9'
    ;


/*
 * URI recognition
 *
 * This is done according to the SparQL grammar, which uses International
 * Resource Identifiers (IRI, RFC3987).
 */

protected /* See LT_OR_URI. */
FULL_URI
    :   '<'! SCHEME ':' (~('>'|' '))* '>'!
    ;

protected
SCHEME
    :   URI_ALPHA
        (URI_ALPHA | URI_DIGIT | '+' | '-' | '.')*;

protected
URI_CHAR
    :   URI_ALPHA | URI_DIGIT | URI_RESERVED | URI_MARK | URI_ESCAPE | '#'
    ;

protected
URI_ALPHA
    :   'a'..'z'
    |   'A'..'Z'
    ;

protected
URI_DIGIT
    :   '0'..'9'
    ;

protected
URI_RESERVED
    :   ';' | '/' | '?' | ':' | '@' | '&' | '=' | '+' | '$' | ','
    ;

protected
URI_MARK
    :   '-' | '_' | '.' | '!' | '~' | '*' | '\'' | '(' | ')'
    ;

protected
URI_ESCAPE
    :   '%'
    ;

LT_OR_URI
    :   ( '<' SCHEME ':' ) => FULL_URI
        { $setType(FULL_URI) }
    |   ( '<' ) => LT
        { $setType(LT) }
    ;
        


/*
 * Character classes from the XML standard, see
 * http://www.w3.org/TR/REC-xml-names
 */

protected
NC_NAME_CHAR
    :   LETTER
    |   UC_DIGIT
    |   '.'
    |   '-'
    |   '_'
    |   COMBINING_CHAR
    |   EXTENDER
    ;

protected
LETTER
    :   BASE_CHAR
    |   IDEOGRAPHIC
    ;

protected
BASE_CHAR
    :   '\u0041'..'\u005A' | '\u0061'..'\u007A' | '\u00C0'..'\u00D6'
    |   '\u00D8'..'\u00F6' | '\u00F8'..'\u00FF' | '\u0100'..'\u0131'
    |   '\u0134'..'\u013E' | '\u0141'..'\u0148' | '\u014A'..'\u017E'
    |   '\u0180'..'\u01C3' | '\u01CD'..'\u01F0' | '\u01F4'..'\u01F5'
    |   '\u01FA'..'\u0217' | '\u0250'..'\u02A8' | '\u02BB'..'\u02C1'
    |   '\u0386' | '\u0388'..'\u038A' | '\u038C' | '\u038E'..'\u03A1'
    |   '\u03A3'..'\u03CE' | '\u03D0'..'\u03D6' | '\u03DA'
    |   '\u03DC' | '\u03DE' | '\u03E0'
    |   '\u03E2'..'\u03F3' | '\u0401'..'\u040C' | '\u040E'..'\u044F'
    |   '\u0451'..'\u045C' | '\u045E'..'\u0481' | '\u0490'..'\u04C4'
    |   '\u04C7'..'\u04C8' | '\u04CB'..'\u04CC' | '\u04D0'..'\u04EB'
    |   '\u04EE'..'\u04F5' | '\u04F8'..'\u04F9' | '\u0531'..'\u0556'
    |   '\u0559' | '\u0561'..'\u0586' | '\u05D0'..'\u05EA'
    |   '\u05F0'..'\u05F2' | '\u0621'..'\u063A' | '\u0641'..'\u064A'
    |   '\u0671'..'\u06B7' | '\u06BA'..'\u06BE' | '\u06C0'..'\u06CE'
    |   '\u06D0'..'\u06D3' | '\u06D5' | '\u06E5'..'\u06E6'
    |   '\u0905'..'\u0939' | '\u093D' | '\u0958'..'\u0961'
    |   '\u0985'..'\u098C' | '\u098F'..'\u0990' | '\u0993'..'\u09A8'
    |   '\u09AA'..'\u09B0' | '\u09B2' | '\u09B6'..'\u09B9'
    |   '\u09DC'..'\u09DD' | '\u09DF'..'\u09E1' | '\u09F0'..'\u09F1'
    |   '\u0A05'..'\u0A0A' | '\u0A0F'..'\u0A10' | '\u0A13'..'\u0A28'
    |   '\u0A2A'..'\u0A30' | '\u0A32'..'\u0A33' | '\u0A35'..'\u0A36'
    |   '\u0A38'..'\u0A39' | '\u0A59'..'\u0A5C' | '\u0A5E'
    |   '\u0A72'..'\u0A74' | '\u0A85'..'\u0A8B' | '\u0A8D'
    |   '\u0A8F'..'\u0A91' | '\u0A93'..'\u0AA8' | '\u0AAA'..'\u0AB0'
    |   '\u0AB2'..'\u0AB3' | '\u0AB5'..'\u0AB9' | '\u0ABD'
    |   '\u0AE0' | '\u0B05'..'\u0B0C' | '\u0B0F'..'\u0B10'
    |   '\u0B13'..'\u0B28' | '\u0B2A'..'\u0B30' | '\u0B32'..'\u0B33'
    |   '\u0B36'..'\u0B39' | '\u0B3D' | '\u0B5C'..'\u0B5D'
    |   '\u0B5F'..'\u0B61' | '\u0B85'..'\u0B8A' | '\u0B8E'..'\u0B90'
    |   '\u0B92'..'\u0B95' | '\u0B99'..'\u0B9A' | '\u0B9C'
    |   '\u0B9E'..'\u0B9F' | '\u0BA3'..'\u0BA4' | '\u0BA8'..'\u0BAA'
    |   '\u0BAE'..'\u0BB5' | '\u0BB7'..'\u0BB9' | '\u0C05'..'\u0C0C'
    |   '\u0C0E'..'\u0C10' | '\u0C12'..'\u0C28' | '\u0C2A'..'\u0C33'
    |   '\u0C35'..'\u0C39' | '\u0C60'..'\u0C61' | '\u0C85'..'\u0C8C'
    |   '\u0C8E'..'\u0C90' | '\u0C92'..'\u0CA8' | '\u0CAA'..'\u0CB3'
    |   '\u0CB5'..'\u0CB9' | '\u0CDE' | '\u0CE0'..'\u0CE1'
    |   '\u0D05'..'\u0D0C' | '\u0D0E'..'\u0D10' | '\u0D12'..'\u0D28'
    |   '\u0D2A'..'\u0D39' | '\u0D60'..'\u0D61' | '\u0E01'..'\u0E2E'
    |   '\u0E30' | '\u0E32'..'\u0E33' | '\u0E40'..'\u0E45'
    |   '\u0E81'..'\u0E82' | '\u0E84' | '\u0E87'..'\u0E88'
    |   '\u0E8A' | '\u0E8D' | '\u0E94'..'\u0E97'
    |   '\u0E99'..'\u0E9F' | '\u0EA1'..'\u0EA3' | '\u0EA5'
    |   '\u0EA7' | '\u0EAA'..'\u0EAB' | '\u0EAD'..'\u0EAE'
    |   '\u0EB0' | '\u0EB2'..'\u0EB3' | '\u0EBD'
    |   '\u0EC0'..'\u0EC4' | '\u0F40'..'\u0F47' | '\u0F49'..'\u0F69'
    |   '\u10A0'..'\u10C5' | '\u10D0'..'\u10F6' | '\u1100'
    |   '\u1102'..'\u1103' | '\u1105'..'\u1107' | '\u1109'
    |   '\u110B'..'\u110C' | '\u110E'..'\u1112' | '\u113C'
    |   '\u113E' | '\u1140' | '\u114C'
    |   '\u114E' | '\u1150' | '\u1154'..'\u1155'
    |   '\u1159' | '\u115F'..'\u1161' | '\u1163'
    |   '\u1165' | '\u1167' | '\u1169'
    |   '\u116D'..'\u116E' | '\u1172'..'\u1173' | '\u1175'
    |   '\u119E' | '\u11A8' | '\u11AB'
    |   '\u11AE'..'\u11AF' | '\u11B7'..'\u11B8' | '\u11BA'
    |   '\u11BC'..'\u11C2' | '\u11EB' | '\u11F0'
    |   '\u11F9' | '\u1E00'..'\u1E9B' | '\u1EA0'..'\u1EF9'
    |   '\u1F00'..'\u1F15' | '\u1F18'..'\u1F1D' | '\u1F20'..'\u1F45'
    |   '\u1F48'..'\u1F4D' | '\u1F50'..'\u1F57' | '\u1F59'
    |   '\u1F5B' | '\u1F5D' | '\u1F5F'..'\u1F7D'
    |   '\u1F80'..'\u1FB4' | '\u1FB6'..'\u1FBC' | '\u1FBE'
    |   '\u1FC2'..'\u1FC4' | '\u1FC6'..'\u1FCC' | '\u1FD0'..'\u1FD3'
    |   '\u1FD6'..'\u1FDB' | '\u1FE0'..'\u1FEC' | '\u1FF2'..'\u1FF4'
    |   '\u1FF6'..'\u1FFC' | '\u2126' | '\u212A'..'\u212B'
    |   '\u212E' | '\u2180'..'\u2182' | '\u3041'..'\u3094'
    |   '\u30A1'..'\u30FA' | '\u3105'..'\u312C' | '\uAC00'..'\uD7A3'
    ;

protected
IDEOGRAPHIC
    :   '\u4E00'..'\u9FA5'
    |   '\u3007'
    |   '\u3021'..'\u3029'
    ;

protected
COMBINING_CHAR
    :   '\u0300'..'\u0345' | '\u0360'..'\u0361' | '\u0483'..'\u0486'
    |   '\u0591'..'\u05A1' | '\u05A3'..'\u05B9' | '\u05BB'..'\u05BD'
    |   '\u05BF' | '\u05C1'..'\u05C2' | '\u05C4' | '\u064B'..'\u0652'
    |   '\u0670' | '\u06D6'..'\u06DC' | '\u06DD'..'\u06DF'
    |   '\u06E0'..'\u06E4' | '\u06E7'..'\u06E8' | '\u06EA'..'\u06ED'
    |   '\u0901'..'\u0903' | '\u093C' | '\u093E'..'\u094C' | '\u094D'
    |   '\u0951'..'\u0954' | '\u0962'..'\u0963' | '\u0981'..'\u0983'
    |   '\u09BC' | '\u09BE' | '\u09BF' | '\u09C0'..'\u09C4'
    |   '\u09C7'..'\u09C8' | '\u09CB'..'\u09CD' | '\u09D7'
    |   '\u09E2'..'\u09E3' | '\u0A02' | '\u0A3C' | '\u0A3E'
    |   '\u0A3F' | '\u0A40'..'\u0A42' | '\u0A47'..'\u0A48'
    |   '\u0A4B'..'\u0A4D' | '\u0A70'..'\u0A71' | '\u0A81'..'\u0A83'
    |   '\u0ABC' | '\u0ABE'..'\u0AC5' | '\u0AC7'..'\u0AC9'
    |   '\u0ACB'..'\u0ACD' | '\u0B01'..'\u0B03' | '\u0B3C'
    |   '\u0B3E'..'\u0B43' | '\u0B47'..'\u0B48' | '\u0B4B'..'\u0B4D'
    |   '\u0B56'..'\u0B57' | '\u0B82'..'\u0B83' | '\u0BBE'..'\u0BC2'
    |   '\u0BC6'..'\u0BC8' | '\u0BCA'..'\u0BCD' | '\u0BD7'
    |   '\u0C01'..'\u0C03' | '\u0C3E'..'\u0C44' | '\u0C46'..'\u0C48'
    |   '\u0C4A'..'\u0C4D' | '\u0C55'..'\u0C56' | '\u0C82'..'\u0C83'
    |   '\u0CBE'..'\u0CC4' | '\u0CC6'..'\u0CC8' | '\u0CCA'..'\u0CCD'
    |   '\u0CD5'..'\u0CD6' | '\u0D02'..'\u0D03' | '\u0D3E'..'\u0D43'
    |   '\u0D46'..'\u0D48' | '\u0D4A'..'\u0D4D' | '\u0D57' | '\u0E31'
    |   '\u0E34'..'\u0E3A' | '\u0E47'..'\u0E4E' | '\u0EB1'
    |   '\u0EB4'..'\u0EB9' | '\u0EBB'..'\u0EBC' | '\u0EC8'..'\u0ECD'
    |   '\u0F18'..'\u0F19' | '\u0F35' | '\u0F37' | '\u0F39' | '\u0F3E'
    |   '\u0F3F' | '\u0F71'..'\u0F84' | '\u0F86'..'\u0F8B'
    |   '\u0F90'..'\u0F95' | '\u0F97' | '\u0F99'..'\u0FAD'
    |   '\u0FB1'..'\u0FB7' | '\u0FB9' | '\u20D0'..'\u20DC'
    |   '\u20E1' | '\u302A'..'\u302F' | '\u3099' | '\u309A'
    ;

protected
UC_DIGIT
    :   '\u0030'..'\u0039' | '\u0660'..'\u0669' | '\u06F0'..'\u06F9'
    |   '\u0966'..'\u096F' | '\u09E6'..'\u09EF' | '\u0A66'..'\u0A6F'
    |   '\u0AE6'..'\u0AEF' | '\u0B66'..'\u0B6F' | '\u0BE7'..'\u0BEF'
    |   '\u0C66'..'\u0C6F' | '\u0CE6'..'\u0CEF' | '\u0D66'..'\u0D6F'
    |   '\u0E50'..'\u0E59' | '\u0ED0'..'\u0ED9' | '\u0F20'..'\u0F29'
    ;

protected
EXTENDER
    :   '\u00B7' | '\u02D0' | '\u02D1' | '\u0387' | '\u0640' | '\u0E46'
    |   '\u0EC6' | '\u3005' | '\u3031'..'\u3035' | '\u309D'..'\u309E'
    |   '\u30FC'..'\u30FE'
    ;

