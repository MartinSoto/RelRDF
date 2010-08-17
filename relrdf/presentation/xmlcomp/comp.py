# -*- coding: utf-8 -*-
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


import re

import xml.etree.ElementTree as et

from itercall import itertask, Call
import diff
import styled


def XML(text):
    if isinstance(text, unicode):
        return et.XML("<?xml version='1.0' encoding='utf-8'?>\n" +
                      text.encode('utf-8'))
    else:
        return et.XML(text)


# Pattern to identify words in text strings.
_DEFAULT_WS_PATTERN = re.compile(r'(\s+)', re.UNICODE)

# Possible token types.
OPEN_TAG = '<Open tag>'
CLOSE_TAG = '<Close tag>'
WORD = '<Data>'

@itertask
def tokenizeString(text, wsPattern=_DEFAULT_WS_PATTERN):
    """Split a string into its component words."""
    for elem in wsPattern.split(text):
        if wsPattern.match(elem) is None:
            yield WORD, elem

@itertask
def tokenizeElem(tree):
    """Produce a list of tokens out of an XML element."""
    yield OPEN_TAG, tree

    if tree.text is not None:
        yield Call(tokenizeString(tree.text))

    for subtree in tree:
        yield Call(tokenizeElem(subtree))

    yield CLOSE_TAG, tree

    if tree.tail is not None:
        yield Call(tokenizeString(tree.tail))


def styledElems(tokens, tagsMap, breakElems):
    curStyle = styled.Style()
    brk = False
    for event, value in tokens:
        if event is OPEN_TAG:
            if brk:
                yield styled.NewLine(styled.Style.fixStyle(curStyle))
                brk = False

            curStyle.append(styled.ElemStyle(value))
            curStyle.sort(key=lambda es: tagsMap[es.elem.tag])
        elif event is CLOSE_TAG:
            curStyle.pop()
            if value.tag in breakElems:
                brk = True
        else:
            if brk:
                yield styled.NewLine(styled.Style.fixStyle(curStyle))
                brk = False

            yield styled.Word(value, styled.Style.fixStyle(curStyle))


@itertask
def synchonizeStyles(curStyle, newStyle):
    # Ignore common portions at the beginning of both styles.
    i = 0
    while i < len(curStyle) and i < len(newStyle) and \
          curStyle[i] == newStyle[i]:
        i += 1

    # Close all elements in the current style up to this point.
    for elemStyle in reversed(curStyle[i:]):
        yield '</%s>' % elemStyle.elem.tag

    # Open all elements in the new style.
    for elemStyle in newStyle[i:]:
        yield str(elemStyle)


class XmlTextDiffStyles(object):
    __slots__ = ('delStyle',
                 'insStyle',)

_protectPtrn = re.compile(r'[<&]')

_protectSubstTable = {
    '<': '&lt;',
    '&': '&amp;'
    }

def _substProtectedChar(match):
    return _protectSubstTable[match.group(0)]

def _protectText(text):
    return _protectPtrn.sub(_substProtectedChar, text)

@itertask
def diffToXml(diffSeq, diffStyles):
    curStyle = styled.Style()
    curStyleDiff = curStyle
    curOpcode = None
    for newOpcode, seq in diffSeq:
        for token in seq:
            newStyle = token.getStyle()
            if newOpcode != curOpcode or newStyle != curStyle:
                if newOpcode == 'unmodif':
                    newStyleDiff = newStyle
                elif newOpcode == 'deleted':
                    newStyleDiff = styled.Style(newStyle)
                    newStyleDiff.append(diffStyles.delStyle)
                elif newOpcode == 'inserted':
                    newStyleDiff = styled.Style(newStyle)
                    newStyleDiff.append(diffStyles.insStyle)
                else:
                    assert False

                curStyle = newStyle
                curOpcode = newOpcode

            yield Call(synchonizeStyles(curStyleDiff, newStyleDiff))
            curStyleDiff = newStyleDiff

            if isinstance(token, styled.Word):
                yield _protectText(unicode(token.data)) + ' '

    # Close any pending elements.
    yield Call(synchonizeStyles(curStyleDiff, styled.Style()))


_htmlTags = ['html', 'ol', 'ul', 'li', 'p', 'img', 'a', 'u', 'b', 'i']

_htmlTagsMap = {}
for i, tag in enumerate(_htmlTags):
    _htmlTagsMap[tag] = i

_htmlBreakElems = set(['p', 'li'])


_htmlDiffStyles = XmlTextDiffStyles()

_delElem = et.Element('span')
_delElem.attrib['class'] = "compOld"
_htmlDiffStyles.delStyle = styled.ElemStyle(_delElem)

_insElem = et.Element('span')
_insElem.attrib['class'] = "compNew"
_htmlDiffStyles.insStyle = styled.ElemStyle(_insElem)

def htmlTextDiff(textA, textB):
    styledA = styledElems(tokenizeElem(XML('<html>%s</html>' % textA)),
                          _htmlTagsMap, _htmlBreakElems)
    styledB = styledElems(tokenizeElem(XML('<html>%s</html>' % textB)),
                          _htmlTagsMap, _htmlBreakElems)

    comp = ''.join(diffToXml(diff.segmentDiff(styledA, styledB),
                             _htmlDiffStyles))

    # Get rid of the html tags.
    return comp[6:-7]


class XmlTextDiff3Styles(object):
    __slots__ = ('delAStyle',
                 'delBStyle',
                 'delABStyle',
                 'insAStyle',
                 'insBStyle')

htmlDiff3Styles = XmlTextDiff3Styles()

_delAElem = et.Element('span')
_delAElem.attrib['class'] = "compDeletedB"
htmlDiff3Styles.delAStyle = styled.ElemStyle(_delAElem)

_delBElem = et.Element('span')
_delBElem.attrib['class'] = "compDeletedC"
htmlDiff3Styles.delBStyle = styled.ElemStyle(_delBElem)

_delABElem = et.Element('span')
_delABElem.attrib['class'] = "compDeletedBC"
htmlDiff3Styles.delABStyle = styled.ElemStyle(_delABElem)

_insAElem = et.Element('span')
_insAElem.attrib['class'] = "compAddedB"
htmlDiff3Styles.insAStyle = styled.ElemStyle(_insAElem)

_insBElem = et.Element('span')
_insBElem.attrib['class'] = "compAddedC"
htmlDiff3Styles.insBStyle = styled.ElemStyle(_insBElem)

@itertask
def xmlTextDiff3Iter(elemOrig, elemA, elemB, diff3Styles=htmlDiff3Styles):
    curStyle = styled.Style()
    curStyleDiff = curStyle
    curOpcode = None

    styledOrig = styledElems(tokenizeElem(elemOrig), _htmlTagsMap,
                             _htmlBreakElems)
    styledA = styledElems(tokenizeElem(elemA), _htmlTagsMap, _htmlBreakElems)
    styledB = styledElems(tokenizeElem(elemB), _htmlTagsMap, _htmlBreakElems)

    for newOpcode, seq in diff.diff3(list(styledOrig), list(styledA),
                                     list(styledB)):
        for token in seq:
            newStyle = token.getStyle()
            if newOpcode != curOpcode or newStyle != curStyle:
                if newOpcode == 'unmodif':
                    newStyleDiff = newStyle
                elif newOpcode == 'deletedA':
                    newStyleDiff = styled.Style(newStyle)
                    newStyleDiff.append(diff3Styles.delAStyle)
                elif newOpcode == 'deletedB':
                    newStyleDiff = styled.Style(newStyle)
                    newStyleDiff.append(diff3Styles.delBStyle)
                elif newOpcode == 'deletedAB':
                    newStyleDiff = styled.Style(newStyle)
                    newStyleDiff.append(diff3Styles.delABStyle)
                elif newOpcode == 'insertedA':
                    newStyleDiff = styled.Style(newStyle)
                    newStyleDiff.append(diff3Styles.insAStyle)
                elif newOpcode == 'insertedB':
                    newStyleDiff = styled.Style(newStyle)
                    newStyleDiff.append(diff3Styles.insBStyle)
                else:
                    assert False, 'unexpected opcode %s' % newOpcode

                curStyle = newStyle
                curOpcode = newOpcode

            yield Call(synchonizeStyles(curStyleDiff, newStyleDiff))
            curStyleDiff = newStyleDiff

            if isinstance(token, styled.Word):
                yield _protectText(unicode(token.data)) + ' '

    # Close any pending elements.
    yield Call(synchonizeStyles(curStyleDiff, styled.Style()))

def xmlTextDiff3(textOrig, textA, textB):
    elemOrig = XML('<html>%s</html>' % textOrig)
    elemA = XML('<html>%s</html>' % textA)
    elemB = XML('<html>%s</html>' % textB)

    comp = ''.join(xmlTextDiff3Iter(elemOrig, elemA, elemB))

    # Get rid of the html tags.
    return comp[6:-7]


compare = htmlTextDiff
compare3 = xmlTextDiff3


