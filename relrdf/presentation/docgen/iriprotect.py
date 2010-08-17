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

"""
Protect IRIs (internationalized URIs) for inclusion in standard URLs.

This module implements a special, ad-hoc system for protecting and
unprotecting special characters in IRIs, in order to make it possible
to use them as part of a larger URL. In an ideal world, it should be
possible to use standard percent encoding (see RFC 3986) of special
IRI characters for this task, but, unfortunately, browser and web
server software tend to handle percent encoding incorrectly (for
example by encoding or decoding more than once) thus damaging encoded
information during processing.

The URI protection process works as follows:

1. Encode the URI (actually IRI) string in UTF-8

2. Encode all characters characters outside the unreserved set (RFC
   3986, sec. 2.3) minus the '~' character, as ``~xx`` where ``xx``
   are two uppercase hexadecimal digits corresponding to the
   character's numeric value. This step is similar to percent
   encoding, but we use a different escape character.
"""

import re

_protectPattern = re.compile(r'[^A-Za-z0-9-._]')

def protectIri(uri):
    # We simply perform standard quoting, and replace the percent
    # sign. Notice that quote_plus (somewhat incorrectly) protects the
    # '~' character.
    return _protectPattern.sub(lambda m: '~%02X' % ord(m.group()),
                               uri.encode('UTF-8'))


class IriDecodeError(Exception):
    pass


_unprotectPattern = re.compile(r'~(.?.?)')
_hexPattern = re.compile(r'[0-9A-Fa-f][0-9A-Fa-f]')

def _decodeChar(match):
    code = match.group(1)
    if not _hexPattern.match(code):
        raise IriDecodeError(_("Invalid escape sequence '~%s'") % code)
    return chr(int(code, base=16))

def unprotectIri(protectedUri):
    # In case we get the protected URI to a unicode string, we convert
    # it to a raw ASCII octet string before unprotect.
    return _unprotectPattern.sub(_decodeChar,
                                 protectedUri.encode('ascii')).decode('UTF-8')


if __name__ == '__main__':
    print protectIri('http://example.com/yeah')
    print protectIri(u'http://example.com/Aktivität')
    print unprotectIri('http~3A~2F~2Fexample.com~2Fyeah')

    try:
        print unprotectIri('http~3A~2F~2Xexample.com~2Fyeah')
    except Exception, e:
        print 'Error:', e

    try:
        print unprotectIri('http~3A~2F~2Fexample.com~2Fyeah~')
    except Exception, e:
        print 'Error:', e

    try:
        print unprotectIri('http~3A~2F~2Fexample.com~2Fyeah~2')
    except Exception, e:
        print 'Error:', e

    print unprotectIri('http~3A~2F~2Fexample.com~2Fyeah~2F')

    def checkRound(iri):
        if unprotectIri(protectIri(iri)) == iri:
            print 'Check round:', iri, 'OK'
        else:
            print 'Check round:', iri, 'Failed'

    checkRound('http://example.com/yeah')
    checkRound('http://example.com/~2F')
    checkRound('http://example.com/The%20feat')
    checkRound('http://example2.com/The%20feat')
    checkRound(u'http://example2.com/Aktivität')
