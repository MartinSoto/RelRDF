# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2010 Fraunhofer-Institut fuer Experimentelles
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

"""Styles and styled elements.

Styled elements are text elements (words and line breaks) having an
associated style, which are used when comparing XML text documents.
The general strategy for comparing documents is to express them first
as sequences of styled text elements, compare the sequences, and
finally convert the comparison results back to XML.

The style of a text element is defined as the list of nested XML tags
(actually elements) that contain the text element, starting from the
root element and going down into its nested elements. So, for example,
a word with style html/body/p/a/b could be a word in bold text inside
a link, in a normal paragrap of an HTML document.

Styles and styled elements are intended to be comparable.
"""

import re


class ElemStyle(object):
    __slots__ = ('elem')

    def __init__(self, elem):
        self.elem = elem

    def __str__(self):
        lst = self.elem.attrib.items()
        lst.sort(key=lambda t: t[0])
        return "<%s%s>" % (self.elem.tag,
                            ''.join((' %s="%s"' % (name, value)
                                     for name, value in lst
                                     if name != 'style')))

    def __hash__(self):
        hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return not self.__eq__(other)


class FixedStyle(tuple):
    def __init__(self, elemLst):
        super(FixedStyle, self).__init__(elemLst)
        self._str = '/'.join(str(e) for e in self)
        self._hash = hash(self._str)

    def __str__(self):
        return self._str

    def __hash__(self):
        return self._hash


class Style(list):
    __slots__ = ()

    def __str__(self):
        return '/'.join(str(e) for e in self)

    def __hash__(self):
        hash(str(self))


    _fixedStyles = {}

    @classmethod
    def fixStyle(cls, style):
        fixed = cls._fixedStyles.get(str(style))
        if fixed is None:
            fixed = FixedStyle(style)
            cls._fixedStyles[str(fixed)] = fixed
        return fixed


class StyledElement(object):
    __slots__ = ('style')

    def __init__(self, style):
        self.style = style

    def __eq__(self, other):
        return self.__class__ == other.__class__ and \
               self.compStr() == other.compStr() and \
               self.getStyle() == other.getStyle()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash('%s+%s' % (self.__class__.__name__, self.compStr()))

    def getStyle(self):
        return self.style


WHITESPACE_PATTERN = re.compile(r'[ \n\t\r]')

class Word(StyledElement):
    __slots__ = ('data',
                 'comp')

    def __init__(self, wordStr, style):
        super(Word, self).__init__(style)
        self.data = wordStr
        self.comp = re.sub(WHITESPACE_PATTERN, '', wordStr)

    def compStr(self):
        return self.comp

    def __str__(self):
        return self.data

    def __repr__(self):
        return '<Word object: %s, %s>' % (repr(self.data), self.style)


class NewLine(StyledElement):
    __slots__ = ()

    def compStr(self):
        return '\n'

    def __str__(self):
        return '\n'

    def __repr__(self):
        return '<NewLine object: %s>' % str(self.style)

