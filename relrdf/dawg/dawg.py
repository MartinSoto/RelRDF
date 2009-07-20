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


import sys

import ns
import tests

import relrdf
from relrdf import basesinks
from relrdf.expression import uri
from relrdf.error import InstantiationError
from relrdf.factory import parseCmdLineArgs

from traceback import format_exc

import textwrap

# Utilities
def isURI(node):
    return isinstance(node, uri.Uri)

class Manifesto:

    __slots__ = ('source',
                 'manifests',
                 'entries',
                 )

    def __init__(self, source):

        # Initialize slots
        self.source = source
        self.manifests = []
        self.entries = []

        # Create parser for ntriples
        from relrdf.modelimport.rdflibparse import RdfLibParser
        parser = RdfLibParser("n3")

        # Parse file
        triples = basesinks.DictSink()
        parser.parse(source, triples)

        # Process triples
        for subject, pred in triples:

            # Include?
            if isURI(pred) and pred == ns.mf.include:
                includes = triples.getList(triples[subject, pred])
                self._handleIncludes(includes)

            # Test entries?
            if isURI(pred) and pred == ns.mf.entries:
                entries = triples.getList(triples[subject, pred])
                self._handleEntries(entries, triples)

    def _handleIncludes(self, files):

        for file in files:

            # Ignore non-URIs
            if not isURI(file):
                continue

            # Parse the included manifest
            manifest = Manifesto(file)
            self.manifests.append(manifest)

    def _handleEntries(self, uris, triples):

        for uri in uris:

            # Ignore non-URIs
            if not isURI(uri):
                continue

            # Create test case
            type = triples.get((uri, ns.rdf.type))
            queryForm = triples.get((uri, ns.qt.queryForm))
            if type == ns.mf.PositiveSyntaxTest:
                entry = tests.SyntaxTest(uri, triples, True)
            elif type == ns.mf.NegativeSyntaxTest:
                entry = tests.SyntaxTest(uri, triples, False)
            elif type == ns.mf.QueryEvaluationTest:
                if queryForm == None:
                    entry = tests.SelectQueryEvaluationTest(uri, triples)
                elif queryForm == ns.qt.QueryConstruct:
                    entry = tests.ConstructQueryEvaluationTest(uri, triples)
                elif queryForm == ns.qt.QueryAsk:
                    entry = tests.AskQueryEvaluationTest(uri, triples)
                else:
                    print "Ignoring unknown query form: ", queryForm
                    continue
            else:
                print "Ignoring unknown test type: ", type
                continue
            self.entries.append(entry)


    def manifestCount(self):
        return 1 + sum([m.manifestCount() for m in self.manifests])

    def entryCount(self):
        return len(self.entries) + sum([m.entryCount() for m in self.manifests])

    def execute(self, ctx):

        if len(self.entries) > 0:
            print "== Executing test cases from %s..." % self.source
            ctx.manifestStart(self.source)

        for entry in self.entries:
            result = entry.execute(ctx)

        for manifest in self.manifests:
            manifest.execute(ctx)

    def filter(self, f):
        self.entries = filter(f, self.entries)
        for manifest in self.manifests:
            manifest.filter(f)

class TestContext(object):

    __slots__ = ('model',
                 'sink',
                 'log',
                 'refSet',

                 '_currentTest',
                 '_results')

    OK = 0
    FAIL = 1
    NO_SUPPORT = 2

    def __init__(self, model, sink, log, refSet = set()):
        self.model = model
        self.sink = sink
        self.log = log
        self.refSet = refSet

        # Valid after testStart until testOk, testNoSupport or testFail is called
        self._currentTest = None

        # Map to receive status of all tests
        self._results = {}

    def _wrap(self, text):
        return "\n".join(["\n    ".join(textwrap.wrap(t, 100)) for t in text.split("\n")])

    def start(self):
        self.log.write("<html><body>\n")
        self.currentTest = None

    def manifestStart(self, source):
        self.log.write("<h1>Test cases from %s</h1>\n" % source)

    def testStart(self, uri, name, testType):

        assert self._currentTest is None
        self._currentTest = uri

        self.log.write("<h2>Case %s</h2>\n" % name)
        self.log.write('<table border="1">\n');
        self.testEntry("Type", testType)

    def testEntry(self, name, value, pre=False, src=None):
        if not isinstance(value, unicode):
            value = unicode(value, errors='ignore')
        if pre:
            text = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            value = "<pre>%s</pre>" % self._wrap(text)
        if not src is None:
            value += '<p>(<a href="%s">%s</a>)</p>' % (src, src)
        self.log.write('<tr><th style="vertical-align:top">%s:</th><td>%s</td></tr>' % (name, value))

    def testOk(self, value=""):
        self.testEnd(self.OK, ('Ok', 'NEW'), 'green', value)

    def testFail(self, value):
        self.testEnd(self.FAIL, ('REGRESSION', 'Fail'), 'red', value)

    def testFailExc(self, msg=None):
        str = ""
        if not msg is None:
            str = "<p>%s:</p>" % msg
        str += "<pre>%s</pre>" % self._wrap(format_exc(1000))
        self.testFail(str)

    def testNoSupport(self, value=""):
        self.testEnd(self.NO_SUPPORT, ('REGRESSION', 'No support'), 'orange', value)

    def testEnd(self, result, statusTags, color, value):

        # Rollback any data put into the database (if any)
        self.sink.rollback()

        # Save result
        assert self._currentTest is not None
        self._results[self._currentTest] = result

        # Format message
        if not isinstance(value, unicode):
            value = unicode(value, errors='ignore')

        # Status tag
        if self._currentTest in self.refSet:
            heading = statusTags[0]
        else:
            heading = statusTags[1]

        # Write log
        self.log.write('<tr><th style="color:%s;vertical-align:top">%s</th><td>%s</td></tr>'
                       % (color, heading, value))
        self.log.write("</table>\n")

        # Done
        self._currentTest = None

    def end(self):
        assert self._currentTest is None
        self.log.write("</body></html>\n")

    def okCount(self):
        return self._results.values().count(self.OK)

    def failCount(self):
        return self._results.values().count(self.FAIL)

    def noSupportCount(self):
        return self._results.values().count(self.NO_SUPPORT)

    def okSet(self):
        return set([uri for (uri, r) in self._results.items() if r == self.OK])

    def regressionCount(self):
        return len(self.refSet - self.okSet())

if __name__ == '__main__':

    TEST_LOG = 'test.log'

    # Command line help
    if len(sys.argv) < 4:
        print "Usage: python dawg.py manifesto.n3 (ref.lst) " \
            ":<model base type> " \
            " [<model base params>] :<model type> [<model params>]"

    # Read manifesto
    manifestoFile = sys.argv[1]
    manifest = Manifesto(manifestoFile)
    entryCount = manifest.entryCount()
    manifestCount = manifest.manifestCount()
    print "Read %d test cases from %d manifest files" \
        % (entryCount, manifestCount)

    # Try to read reference list
    refSet = set()
    argv = sys.argv[2:]
    if sys.argv[2][0] != ':':
        try:
            refFile = open(sys.argv[2], "r")
            refSet = set([s.rstrip() for s in refFile.readlines()])
            refFile.close()
            argv = argv = sys.argv[3:]
        except IOError, e:
            print >> sys.stderr, "Could not read reference list: %s" % e
            sys.exit(1)

    # Get model base and sink
    try:

        # Open model
        baseType, baseArgs = parseCmdLineArgs(argv, 'model base')
        modelBase = relrdf.getModelBase(baseType, **baseArgs)

        # Create graph to run test cases in
        baseGraphUri = manifest.source
        modelBase.lookupGraphId(baseGraphUri, create=True)

        # Open model
        modelType, modelArgs = parseCmdLineArgs(argv, 'model')
        modelArgs['baseGraph'] = baseGraphUri
        model = modelBase.getModel(modelType, **modelArgs)

        # Open sink
        sink = model.getSink()

    except InstantiationError, e:
        print >> sys.stderr, ("error: %s") % e
        sys.exit(1)

    # Open test context
    ctx = TestContext(model, sink, open("log.html", "w"), refSet)

    # Execute test cases
    successCount = manifest.execute(ctx)

    # Gather some statistics
    totalCount = manifest.entryCount()
    okCount = ctx.okCount()
    noSupportCount = ctx.noSupportCount()
    regressionCount = ctx.regressionCount()
    newCount = okCount - len(refSet) + regressionCount

    # Give statistics
    print "== %d/%d test cases succeeded!" % (okCount, totalCount)
    print "== (%d new, %d regressions, %d not supported)" % (newCount, regressionCount, noSupportCount)

    ctx.end()

    # Write log
    refFile = open(TEST_LOG, "w")
    refFile.writelines([s + '\n' for s in ctx.okSet()])
    refFile.close()
    print "Successful test cases were written to " + TEST_LOG + "\n"


