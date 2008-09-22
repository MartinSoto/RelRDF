# Adapted from rdflib
#
# Original copyright notice:
#
# Copyright (c) 2002, Daniel Krech, http://eikeon.com/
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
#   * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following
# disclaimer in the documentation and/or other materials provided
# with the distribution.
#
#   * Neither the name of Daniel Krech nor the names of its
# contributors may be used to endorse or promote products derived
# from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# From: http://www.w3.org/TR/REC-xml#NT-CombiningChar
#
# * Name start characters must have one of the categories Ll, Lu, Lo,
#   Lt, Nl.
#
# * Name characters other than Name-start characters must have one of
#   the categories Mc, Me, Mn, Lm, or Nd.
#
# * Characters in the compatibility area (i.e. with character code
#   greater than #xF900 and less than #xFFFE) are not allowed in XML
#   names.
#
# * Characters which have a font or compatibility decomposition
#   (i.e. those with a "compatibility formatting tag" in field 5 of the
#   database -- marked by field 5 beginning with a "<") are not allowed.
#
# * The following characters are treated as name-start characters rather
#   than name characters, because the property file classifies them as
#   Alphabetic: [#x02BB-#x02C1], #x0559, #x06E5, #x06E6.
#
# * Characters #x20DD-#x20E0 are excluded (in accordance with Unicode
#   2.0, section 5.14).
#
# * Character #x00B7 is classified as an extender, because the property
#   list so identifies it.
#
# * Character #x0387 is added as a name character, because #x00B7 is its
#   canonical equivalent.
#
# * Characters ':' and '_' are allowed as name-start characters.
#
# * Characters '-' and '.' are allowed as name characters.

from unicodedata import category, decomposition

NAME_START_CATEGORIES = ["Ll", "Lu", "Lo", "Lt", "Nl"]
NAME_CATEGORIES = NAME_START_CATEGORIES + ["Mc", "Me", "Mn", "Lm", "Nd"]
ALLOWED_NAME_CHARS = [u"\u00B7", u"\u0387", u"-", u".", u"_"]

# http://www.w3.org/TR/REC-xml-names/#NT-NCName
#  [4] NCName ::= (Letter | '_') (NCNameChar)* /* An XML Name, minus
#      the ":" */
#  [5] NCNameChar ::= Letter | Digit | '.' | '-' | '_' | CombiningChar
#      | Extender

def is_ncname(name):
    first = name[0]
    if first=="_" or category(first) in NAME_START_CATEGORIES:
        for i in xrange(1, len(name)):
            c = name[i]
            if not category(c) in NAME_CATEGORIES:
                if c in ALLOWED_NAME_CHARS:
                    continue
                return 0
            #if in compatibility area
            #if decomposition(c)!='':
            #    return 0

        return 1
    else:
        return 0

XMLNS = "http://www.w3.org/XML/1998/namespace"

def split_uri(uri):
    if uri.startswith(XMLNS):
        return (XMLNS, uri.split(XMLNS)[1])
    length = len(uri)
    for i in xrange(0, length):
        c = uri[-i-1]
        if not category(c) in NAME_CATEGORIES:
            if c in ALLOWED_NAME_CHARS:
                continue
            for j in xrange(-1-i, length):
                if category(uri[j]) in NAME_START_CATEGORIES or uri[j]=="_":
                    ns = uri[:j]
                    if not ns:
                        break
                    ln = uri[j:]
                    return (ns, ln)
            break
    raise Exception("Can't split '%s'" % uri)



