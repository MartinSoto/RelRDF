# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2009 Fraunhofer-Institut fuer Experimentelles
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


import cgi

from relrdf import commonns
from relrdf.expression import uri, literal
from relrdf.util import nsshortener


class SerializationError(Exception):
    pass


class RdfXmlSerializer(object):
    __slots__ = ('stream',
                 'namespaces',

                 'qnameShrt',
                 'entityShrt')

    def __init__(self, stream, namespaces):
        self.stream = stream
        if 'rdf' not in namespaces:
            self.namespaces = dict(namespaces)
            self.namespaces['rdf'] = commonns.rdf
        else:
            self.namespaces = namespaces

        self.qnameShrt = \
            nsshortener.NamespaceUriShortener(shortFmt='%s:%s',
                                              longFmt='%s')
        self.qnameShrt.addPrefixes(self.namespaces)
        self.entityShrt = \
            nsshortener.NamespaceUriShortener(shortFmt='&%s;%s',
                                              longFmt='%s')
        self.entityShrt.addPrefixes(self.namespaces)

        # Create the header and declare the namespaces.
        self.stream.write("<?xml version='1.0' encoding='UTF-8'?>\n\n")

        self.stream.write("<!DOCTYPE rdf:RDF [\n")
        for prefix, uri in self.namespaces.items():
            self.stream.write("  <!ENTITY %s '%s'>\n" % (prefix, uri))
        self.stream.write("]>\n\n")

        self.stream.write('<rdf:RDF\n')
        for prefix in self.namespaces.keys():
            self.stream.write('  xmlns:%s="&%s;"\n' % (prefix, prefix))
        self.stream.write(">\n")

    def triple(self, subject, pred, object):
        sPred = self.qnameShrt.shortenUri(pred)
        if sPred == pred:
            # FIXME: This should try to create a namespace for the URI.
            raise SerializationError, \
                  "Predicate '%s' cannot be serialized to XML RDF" % pred

        self.stream.write('  <rdf:Description rdf:about="%s">\n' %
                     self.entityShrt.shortenUri(subject))

        self.stream.write('    <%s' % sPred)

        if isinstance(object, literal.Literal):
            self.stream.write('>%s</%s>\n' %
                              (cgi.escape(unicode(object), True), sPred))
        else:
            self.stream.write(' rdf:resource="%s" />\n' %
                              self.entityShrt.shortenUri(unicode(object)))

        self.stream.write('  </rdf:Description>\n')

    def close(self):
        self.stream.write('</rdf:RDF>\n')

