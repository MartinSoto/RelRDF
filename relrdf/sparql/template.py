"""(More) Secure query template for SPARQL."""

import string
import StringIO
import re

import antlr
import SparqlLexer

from relrdf.localization import _
from relrdf import TemplateError
from relrdf import Uri, Literal


class Template(string.Template):
    """A string template for SPARQL queries, with safe substitution.

    This is an extension of the standard Python `string.Template`
    class, that automatically (and hopefully securely) converts
    substituted values to their SPARQL representations. Values can be
    Python numbers (instances of `int` or `float`, converted to SPARQL
    numbers), strings (instances of `str` or `unicode`, converted to
    SPARQL string literals) or instances of RelRDF's `Uri` (converted
    to SPARQL URI reference) and `Literal` (converted to a numeric or
    string literal depending on the type.)

    For enhanced security against code injection, converted values are
    checked using the actual SPARQL lexer, in order to guarantee that
    they will be properly recognized by the parser when they are part
    of the final query. They are also inserted in the query with
    leading and trailing spaces to reduce the risk of them being
    merged with other tokens. Notice that substitutions inside a
    string could still completely confuse the parser and should be
    avoided.
    """

    __slots__ = ()

    queryLanguage = 'sparql'

    def substitute(self, mapping=None, **keywords):
        if mapping is None:
            mapping = dict(keywords)
        else:
            mapping = dict(mapping)
            mapping.update(keywords)

        self._prepareMapping(mapping)

        try:
            return super(Template, self).substitute(mapping)
        except KeyError, e:
            raise TemplateError(_("No value given for field '%s'") % e.args[0])

    def safe_substitute(self, mapping=None, **keywords):
        if mapping is None:
            mapping = dict(keywords)
        else:
            mapping = dict(mapping)
            mapping.update(keywords)

        self._prepareMapping(mapping)

        try:
            return super(Template, self).safe_substitute(mapping)
        except KeyError, e:
            raise TemplateError(_("No value given for field '%s'") % e.args[0])

    def _prepareMapping(self, mapping):
        for ident, value in mapping.items():
            if isinstance(value, Literal):
                lang = value.lang
                typeUri = value.typeUri
                value = self._protectString(value)

                self._checkToken(value, SparqlLexer.STRING_LITERAL2)
                if lang is not None:
                    langTag = '@' + lang
                    self._checkToken(langTag, SparqlLexer.LANGTAG)
                    value = value + langTag
                elif typeUri is not None:
                    typeUri = '<' + unicode(typeUri) + '>'
                    self._checkToken(typeUri, SparqlLexer.Q_IRI_REF)
                    value = value + '^^' + typeUri
            elif isinstance(value, Uri):
                value = '<%s>' % unicode(value)
                self._checkToken(value, SparqlLexer.Q_IRI_REF)
            elif isinstance(value, int) or isinstance(value, long):
                value = str(value)
                self._checkToken(value, SparqlLexer.INTEGER)
            elif isinstance(value, float):
                value = str(value)
                self._checkToken(value, SparqlLexer.DECIMAL,
                                 SparqlLexer.DOUBLE)
            elif isinstance(value, basestring):
                value = self._protectString(value)
            else:
                raise TemplateError(_("Value '%s' could not be "
                                      "automatically converted to SPARQL") %
                                    repr(value))

            mapping[ident] = ' %s ' % value

        return mapping

    _protectPattern = re.compile(r'[\t\b\n\r\f"\'\\]')

    # Keys and values look identical, but they aren't.
    _protectMap = {
        '\t': r'\t',
        '\b': r'\b',
        '\n': r'\n',
        '\r': r'\r',
        '\f': r'\f',
        '\"': r'\"',
        '\'': r'\'',
        '\\': r'\\',
        }

    def _protectString(self, obj):
        def repl(match):
            return self._protectMap[match.group(0)]
        return '"' + self._protectPattern.sub(repl, unicode(obj)) + '"'

    _lexer = SparqlLexer.Lexer()

    def _checkToken(self, value, *tokenTypes):
        stream = StringIO.StringIO(value)
        self._lexer.setInput(stream)

        try:
            tokens = tuple(self._lexer)
        except antlr.TokenStreamRecognitionException:
            raise TemplateError(_("Invalid value '%s'") % value)

        if len(tokens) != 1 or tokens[0].type not in tokenTypes:
            raise TemplateError(_("Invalid value '%s'") % value)

        return tokens[0].text


if __name__ == '__main__':
    from relrdf.commonns import xsd

    t = Template('')

    str1 = """This is a long
    string with \t\b\r\f some
    cuts in it and some interesting stuff like \\ or 'this'
    and \"this\"."""

    str1p = t._protectString(str1)

    assert t._checkToken(str1p, SparqlLexer.STRING_LITERAL2) == str1

    t = Template('***$value1+++')
    print t.substitute(value1=str1)

    t = Template('***$value1+++')
    print t.substitute(dict(value1=str1))

    t = Template('***$value1 $value2+++')
    print t.substitute(dict(value1=str1), value2='xxyy')

    t = Template('***$value1+++')
    v = 'xxyy'
    print t.substitute(dict(value1=v))

    t = Template('***$value1+++')
    v = 12
    print t.substitute(dict(value1=v))

    t = Template('***$value1+++')
    v = 3.4
    print t.substitute(dict(value1=v))

    t = Template('***$value1+++')
    v = 3.4e25
    print t.substitute(dict(value1=v))

    t = Template('***$value1+++')
    v = Literal('xxyy')
    print t.substitute(dict(value1=v))

    t = Template('***$value1+++')
    v = Literal('hola', lang='es')
    print t.substitute(dict(value1=v))

    t = Template('***$value1+++')
    v = Literal('12', typeUri=xsd.double)
    print t.substitute(dict(value1=v))

    t = Template('***$value1+++')
    v = Literal(12)
    print t.substitute(dict(value1=v))

    t = Template('***$value1+++')
    v = Literal(3.4)
    print t.substitute(dict(value1=v))

    t = Template('***$value1+++')
    v = Literal(3.4e25)
    print t.substitute(dict(value1=v))

    t = Template('***$value1+++')
    v = Uri('http://example.com/test')
    print t.substitute(dict(value1=v))

    t = Template('***$value1+++')
    v = Uri('dskjdksj>>>')
    print t.substitute(dict(value1=v))
