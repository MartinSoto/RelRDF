import codecs
from xml.sax.saxutils import escape

from relrdf.localization import _
from relrdf import Uri, Literal
from relrdf import SerializationError
from relrdf import ns, NamespaceUriShortener


class RdfXmlSerializer(object):
    __slots__ = ('shortener',
                 'writer')

    def __init__(self, fileName, model, encoding='utf-8'):
        self.shortener = NamespaceUriShortener()
        self.shortener.addPrefixes(model.getPrefixes())
        self.shortener['rdf'] = ns.rdf
        self.shortener['rdfs'] = ns.rdfs

        self.writer = codecs.getwriter(encoding)(file(fileName, 'w'))

        stmts = model.query('sparql', """
            construct {?s ?p ?o}
            where {?s ?p ?o}
            order by ?s ?p ?o
            """)

        # XML declaration.
        self.writeln('<?xml version="1.0" encoding="%s"?>' % encoding)

        # Open the main element and introduce the namespaces.
        self.write('<rdf:RDF')
        bindings = self.shortener.items()
        bindings.sort()
        for prefix, uri in bindings:
            self.writeln(' xmlns:%s="%s"' % (prefix, uri))
        self.writeln('>')

        curSubject = None
        for subject, predicate, object in stmts:
            if curSubject != subject:
                if curSubject is not None:
                    # Close the previous description element.
                    self.writeln('</rdf:Description>')

                curSubject = subject

                # Open a new description.
                self.writeln('<rdf:Description rdf:about="%s">' % subject)

            # Open the property tag.
            prefix, suffix = self.shortener.breakUri(predicate)
            if prefix is None:
                # Predicates must be shortened.
                raise SerializationError(_("Unable to shorten predicate '%s'")
                                         % predicate)
            self.write('<%s:%s' % (prefix, suffix))

            # Output the property value and close the tag/element.
            if isinstance(object, Uri):
                self.writeln(' rdf:resource="%s" />' % object)
            elif isinstance(object, Literal):
                self.writeln('>%s</%s:%s>' % (escape(object), prefix, suffix))

        if curSubject is not None:
            # Close the previous description element.
            self.writeln('</rdf:Description>')

        # Close the main element.
        self.writeln( "</rdf:RDF>" )

    def write(self, text):
        self.writer.write(text)

    def writeln(self, text):
        self.writer.write(text + '\n')
