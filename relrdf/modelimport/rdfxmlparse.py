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

from xml.sax import make_parser
from xml.sax.saxutils import handler
from xml.sax.handler import ErrorHandler

from relrdf.expression import uri, blanknode, literal

from RDFXMLHandler import RDFXMLHandler


class SinkToStore(object):
    __slots__ = ('sink')

    def __init__(self, sink):
        self.sink = sink

    def bind(self, prefix, namespace, override=True):
        # Ignore.
        pass

    def add(self, (subject, pred, object)):
        if not isinstance(object, uri.Uri) and \
           not isinstance(object, blanknode.BlankNode) and \
           not isinstance(object, literal.Literal):
            object = literal.Literal(object)

        self.sink.triple(subject, pred, object)


class RdfXmlParser(object):
    __slots__ = ('_parser',)

    @staticmethod
    def _create_parser(store):
        parser = make_parser()

        # Workaround for bug in expatreader.py. Needed when
        # expatreader is trying to guess a prefix.
        parser.start_namespace_decl("xml",
                                    "http://www.w3.org/XML/1998/namespace")
        parser.setFeature(handler.feature_namespaces, 1)
        rdfxml = RDFXMLHandler(store)
        parser.setContentHandler(rdfxml)
        parser.setErrorHandler(ErrorHandler())

        return parser

    def parse(self, source, sink, **args):
        self._parser = self._create_parser(SinkToStore(sink))
        content_handler = self._parser.getContentHandler()

        preserve_bnode_ids = args.get("preserve_bnode_ids", None)
        if preserve_bnode_ids is not None:
            content_handler.preserve_bnode_ids = preserve_bnode_ids

        self._parser.parse(source)


if __name__ == '__main__':
    import sys
    from relrdf.basesinks import PrintSink

    source = sys.argv[1]
    sink = PrintSink()

    parser = RdfXmlParser()
    parser.parse(source, sink)
