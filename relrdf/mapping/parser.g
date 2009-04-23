/* This file is part of RelRDF, a library for storage and
 * comparison of RDF models.
 *
 * Copyright (C) 2005-2009, Fraunhofer Institut Experimentelles
 * Software Engineering (IESE).
 *
 * RelRDF is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA. 
*/

header {
    from relrdf.commonns import rdf, xsd
    from relrdf.expression import nodes

    import parser
    import sqlnodes
    import schema
    import macro
    import valueref
}

options {
    language = "Python";
}

/*----------------------------------------------------------------------
 * Parser
 *--------------------------------------------------------------------*/

class SchemaParser extends Parser("parser.Parser");

options {
    k=2;
    defaultErrorHandler=false;
}


// This symbol won't normally be used directly, but is necessary for
// the parser to be able to recognize single expressions.
main returns [value]
    :   value=schemaDef
    |   value=expression
    ;


schemaDef returns [sch]
    :   { self.schema = schema.Schema(); }
        (   defObj=declaration sm:SEMICOLON
            { defObj.setExtentsEndFromToken(sm); \
              self.schema.addDef(defObj); }
        )+
        { sch = self.schema }
    ;

declaration returns [defObj]
    :   defObj=tableDecl
    |   defObj=indexDecl
    |   defObj=macroDef
    |   defObj=mappingDecl
    ;


tableDecl returns [table]
    :   tb:"table" name=objName
        { table = schema.Table(name); \
          table.setExtentsStartFromToken(tb, self); }
        LPAREN columnDeclList[table] RPAREN
    ;

objName returns [name]
    :   id:IDENTIFIER
        { name = nodes.Literal(id.getText()); \
          name.setExtentsFromToken(id, self); }
    ;

columnDeclList[table]
    :   columnDecl[table] ( COMMA columnDecl[table] )*
    ;

columnDecl[table]
    :   name=objName type=columnType opts=columnOptions
        { colObj = schema.Column(name, type, opts); \
          table.addColumn(colObj); }
    ;

columnType returns [expr]
    :   expr=iriRef
    ;

columnOptions returns [opts]
    :   { opts = set(); }
        (   option=columnOption
            { opts.add(option); }
        )*
    ;

columnOption returns [option]
    :   "notnull"
        { option = schema.COL_OPT_NOT_NULL; }
    |   "autoincrement"
        { option = schema.COL_OPT_AUTO_INCR; }
    ;


indexDecl returns [index]
    :   id:"index" name=objName tableName=objName
        { index = schema.Index(name, self.schema.getTable(tableName)); \
          index.setExtentsStartFromToken(id, self); }
        columnList[index] indexOptions[index]
    ;

columnList[index]
    :   LPAREN colName=objName
        { index.addColumn(colName); }
        (   COMMA colName=objName
            { index.addColumn(colName); }
        )* RPAREN
    ;

indexOptions[index]
    :   (   opt=indexOption
            { index.options.add(opt); }
        )*
    ;

indexOption returns [opt]
    :   "unique"
        { option = schema.INDEX_OPT_UNIQUE; }
    |   "primary"
        { option = schema.INDEX_OPT_PRIMARY; }
    ;


macroDef returns [macroDef]
    :   df:"def" name=objName params=macroParamList expr=expression
        { closure = macro.MacroClosure(params, self.mainEnv, expr); \
          macroDef = schema.MacroDef(name, closure); \
          macroDef.setExtentsStartFromToken(df, self); }
    ;

macroParamList returns [params]
    :   LPAREN
        { params = []; }
        (   param=macroParam
            { params.append(param); }
            (   COMMA param=macroParam
                { params.append(param); }
            )*
        )?
        RPAREN
    ;

macroParam returns [param]
    :   v:VAR
        { param = v.getText(); }
    ;


mappingDecl returns [mappingDef]
    :   "mapping" name=objName params=macroParamList
        { mappingDef = schema.MappingDef(name, params); }
        matchList[mappingDef]
        "default" expr=expression
        { mappingDef.setDefault(expr); }
    ;

matchList[mappingDef]
    :   (   "match" pattern=matchPattern
            { cond = None; }
            (   "on" LPAREN cond=expression RPAREN
            )?
            expr=expression
            { mappingDef.addMatch(pattern, expr, cond); }
        )*
    ;

matchPattern returns [pattern]
    :   LPAREN
        graph=matchPatternElem COMMA
        subj=matchPatternElem COMMA
        pred=matchPatternElem COMMA
        obj=matchPatternElem
        RPAREN
        { pattern = [graph, subj, pred, obj]; }
    ;

matchPatternElem returns [elem]
    :   v:VAR
        { elem = v.getText(); }
    |   DOT
        { elem = None; }
    ;


expression returns [expr]
    :   expr=mapTableExpression
    ;

mapTableExpression returns [expr]
    :   expr=selectTableExpression
    |   m:"mapto" rp:LPAREN specs=mapList RPAREN expr=mapTableExpression
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
    :   expr=expression
        { colName = ""; }
        (   "as" cn:IDENTIFIER
            { colName = cn.getText() }
        )?
        { specs[0].append(expr); \
          specs[1].append(colName); }
    ;

selectTableExpression returns [expr]
    :   expr=productTableExpression
        (   "on" pred=conditionalOrExpression
            { expr = nodes.Select(expr, pred) }
        )?
    ;

productTableExpression returns [expr]
    :   expr=conditionalOrExpression
        (   "cross" expr2=productTableExpression
            { expr = nodes.Product(expr, expr2) }
        )?
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
            { expr = nodes.Plus(expr, mult); }
        |   MINUS mult=multiplicativeExpression
            { expr = nodes.Minus(expr, mult); }
        )*
    ;

multiplicativeExpression returns [expr]
    :   expr=unaryExpression
        (   TIMES unary=unaryExpression
            { expr = nodes.Times(expr, unary); }
        |   DIV unary=unaryExpression
            { expr = nodes.DividedBy(expr, unary); }
        )*
    ;

unaryExpression returns [expr]
    :   on:OP_NOT prim=primaryExpression
        { expr = nodes.Not(prim); \
          expr.setExtentsStartFromToken(on, self); }
    |   plus:PLUS prim=primaryExpression
        { expr = prim; }
    |   minus:MINUS prim=primaryExpression
        { expr = nodes.UMinus(prim); \
          expr.setExtentsStartFromToken(minus, self); }
    |   expr=primaryExpression
    ;

primaryExpression returns [expr]
    :   expr=brackettedExpression
    |   expr=tableRef
    |   expr=columnRef
    |   expr=functionCall
    |   expr=ifExpr
    |   expr=valueMapping
    |   expr=valueRef
    |   expr=iriRef
    |   expr=macroVar
    |   expr=rdfLiteral
    |   expr=numericLiteral
    |   expr=booleanLiteral
    ;

brackettedExpression returns [expr]
    :   LPAREN expr=expression RPAREN
    ;

tableRef returns [expr]
    :   t:IDENTIFIER
        { expr = sqlnodes.SqlRelation(t.getText(), t.getText()); \
          expr.setExtentsFromToken(t, self) }
        (   i:IDENTIFIER
            { expr.incarnation = i.getText(); \
              expr.setExtentsEndFromToken(i) }
        )?
    ;

columnRef returns [expr]
    :   t:IDENTIFIER DOT cn:IDENTIFIER
        { expr = sqlnodes.SqlFieldRef(t.getText(), cn.getText()); \
          expr.setExtentsStartFromToken(t, self); \
          expr.setExtentsEndFromToken(cn) }
    ;


functionCall returns [expr]
    :   id:IDENTIFIER
        { expr = self.createCallExpr(id.getText()); \
          expr.setExtentsStartFromToken(id, self); }
        argList[expr]
    ;

argList[callExpr]
    :   (   LPAREN
            (   param=expression
                { callExpr.append(param) }
                (   COMMA param=expression
                    { callExpr.append(param) }
                )*
            )?
            rp:RPAREN
            { callExpr.setExtentsEndFromToken(rp) }
        )
    ;


ifExpr returns [expr]
    :   ift:"if" LPAREN cond=expression COMMA
        elseExpr=expression COMMA
        thenExpr=expression RPAREN
        { expr = nodes.If(cond, elseExpr, thenExpr); \
          expr.setExtentsStartFromToken(ift, self); }
    ;


valueMapping returns [expr]
    :   vm:"valuemapping" LPAREN
        "inttoext" LPAREN param1=macroParam RPAREN expr1=expression
        "exttoint" LPAREN param2=macroParam RPAREN expr2=expression
        RPAREN
        { intToExtCls = macro.MacroClosure([param1], None, expr1); \
          extToIntCls = macro.MacroClosure([param2], None, expr2); \
          expr = valueref.MacroValueMapping(intToExtCls, extToIntCls); \
          expr.setExtentsStartFromToken(vm, self);
        }
    ;

valueRef returns [expr]
    :   r:"ref" LPAREN mapping=expression COMMA expr=expression RPAREN
        { expr = valueref.ValueRef(mapping, expr); \
          expr.setExtentsStartFromToken(r, self); }
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
        { expr = self.makeTypedLiteral(int(i.getText()), xsd.integer); \
          expr.setExtentsFromToken(i, self)}
    |   de:DECIMAL
        { expr = self.makeTypedLiteral(float(de.getText()), xsd.decimal); \
          expr.setExtentsFromToken(de, self)}
    |   db:DOUBLE
        { expr = self.makeTypedLiteral(float(db.getText()), xsd.double); \
          expr.setExtentsFromToken(db, self)}
    ;

booleanLiteral returns [expr]
    :   t:"true"
        { expr = self.makeTypedLiteral(True, xsd.boolean); \
          expr.setExtentsFromToken(t, self)}
    |   f:"false"
        { expr = self.makeTypedLiteral(False, xsd.boolean); \
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


macroVar returns [expr]
    :   v:VAR
        { expr = macro.MacroVar(v.getText()); }
    ;


/*----------------------------------------------------------------------
 * Lexical Analyzer
 *--------------------------------------------------------------------*/

class SchemaLexer extends Lexer;

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

COMMENT
    :   '#' ( ~( '\n' | '\r' ) )*
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

LPAREN
    :   '('
    ;

RPAREN
    :   ')'
    ;

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

VAR
    :   '$'! IDENTIFIER
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

