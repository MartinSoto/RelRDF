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
import os.path
import hashlib
import codecs

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

def md5(uri):
    m = hashlib.md5()
    m.update(uri.encode('utf-8'))
    return m.hexdigest()


class Manifesto(object):

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
        return len(self.entries) + sum([m.entryCount()
                                        for m in self.manifests])

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

    __slots__ = ('modelBase',
                 'baseGraphUri',
                 'destPath',
                 'refSet',

                 '_mainLog',
                 '_currentTest',
                 '_currentLog',
                 '_results')

    OK = 0
    FAIL = 1
    NO_SUPPORT = 2

    def __init__(self, modelBase, baseGraphUri, destPath, refSet = set()):
        self.modelBase = modelBase
        self.baseGraphUri = baseGraphUri
        self.destPath = destPath
        self.refSet = refSet

        # Valid after testStart until testOk, testNoSupport or
        # testFail is called.
        self._currentTest = None

        # Map to receive status of all tests.
        self._results = {}

    def _wrap(self, text):
        return "\n".join(["\n    ".join(textwrap.wrap(t, 100))
                          for t in text.split("\n")])

    def _htmlHeading(self, title):
        return \
            '<?xml version="1.0" encoding="utf-8"?>\n' \
            '<html xmlns="http://www.w3.org/1999/xhtml">\n' \
            '<head>\n' \
            '<title>%s</title>\n' \
            '<style type="text/css">\n' \
            '  th {text-align: left;]\n' \
            '</style>\n' \
            '</head>\n' \
            '<body>\n' % title

    def start(self):
        if os.path.exists(self.destPath):
            if not os.path.isdir(self.destPath):
                raise IOError("Destination path '%s' exists but is not "
                              "a directory" % self.destPath)
        else:
            # Try to create the destination directory.
            os.makedirs(self.destPath)

        self._currentTest = None
        self._currentLog = None

        # Start the main log.
        self._mainLog = codecs.open(os.path.join(self.destPath,
                                                 'index.html'),
                                    'w', 'utf-8')

        self._mainLog.write(self._htmlHeading('Test Report'))
        self._mainLog.write("<h2>Test Report</h2>\n")
        self._mainLog.write('<table border="1">\n');

    def manifestStart(self, source):
        self._mainLog.write('<tr><th colspan="2">Test cases from %s'
                            '</th></tr>\n' % source)
        self._mainLog.write('<tr><th>Case</th><th>Result</th></tr>\n')

    def testStart(self, uri, name, testType):
        assert self._currentTest is None
        self._currentTest = uri

        # Make a file name for the test.
        logName = 'log_%s.html' % md5(uri)

        # Start the summary entry for the test.
        self._mainLog.write('<tr><td><a href="%s">%s</a></td>' %
                            (logName, name))

        # Open the log file for this test.
        assert self._currentLog is None
        self._currentLog = codecs.open(os.path.join(self.destPath,
                                                    logName),
                                       'w', 'utf-8')

        self._currentLog.write(self._htmlHeading(name))
        self._currentLog.write("<h2>Case %s</h2>\n" % name)
        self._currentLog.write('<table border="1">\n');
        self.testEntry("Type", testType)

    def testEntry(self, name, value, pre=False, src=None):
        if not isinstance(value, unicode):
            value = unicode(value, errors='ignore')
        if pre:
            text = value.replace('&', '&amp;').replace('<', '&lt;') \
                .replace('>', '&gt;')
            value = "<pre>%s</pre>" % self._wrap(text)
        if not src is None:
            value += '<p>(<a href="%s">%s</a>)</p>' % (src, src)
        self._currentLog.write('<tr><th style="vertical-align:top">%s:'
                       '</th><td>%s</td></tr>' % (name, value))

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
        self.testEnd(self.NO_SUPPORT, ('REGRESSION', 'No support'),
                     'orange', value)

    def testEnd(self, result, statusTags, color, value):
        # Rollback any changes done on database (if any).
        self.modelBase.rollback()

        # Save results.
        assert self._currentTest is not None
        self._results[self._currentTest] = result

        # Format message.
        if not isinstance(value, unicode):
            value = unicode(value, errors='ignore')

        # Status tag.
        if self._currentTest in self.refSet:
            heading = statusTags[0]
        else:
            heading = statusTags[1]

        # Finish test log.
        self._currentLog.write('<tr><th style="color:%s;'
                               'vertical-align:top">%s</th><td>%s</td></tr>'
                               % (color, heading, value))
        self._currentLog.write("</table>\n")

        self._currentLog.write("</body></html>\n")

        self._currentLog.close()
        self._currentLog = None

        # Write the result to the summary and close the row.
        self._mainLog.write('<td style="color:%s;'
                            'vertical-align:top">%s</td></tr>\n'
                            % (color, heading))

        # Done
        self._currentTest = None

    def end(self, referenceCount):
        assert self._currentTest is None

        # Gather some statistics.
        #totalCount = manifest.entryCount()
        totalCount = len(self._results)
        okCount = self.okCount()
        noSupportCount = self.noSupportCount()
        failedCount = totalCount - okCount - noSupportCount
        regressionCount = self.regressionCount()
        newCount = okCount - (referenceCount - regressionCount)

        # Print out statistics.
        print "== %d/%d test cases succeeded!" % (okCount, totalCount)
        print "== (%d new, %d regressions, %d not supported)" % \
            (newCount, regressionCount, noSupportCount)

        self._mainLog.write('<tr><th colspan="2">Statistics</th></tr>\n')
        self._mainLog.write('<tr><th>Total</th>'
                            '<td>%d</td></tr>\n' % totalCount)
        self._mainLog.write('<tr><th>Succeded</th>'
                            '<td>%d (%d%%)</td></tr>\n' %
                            (okCount,
                             round(100 * okCount / float(totalCount))))
        self._mainLog.write('<tr><th>Failed</th>'
                            '<td>%d (%d%%)</td></tr>\n' %
                            (failedCount,
                             round(100 * failedCount / float(totalCount))))
        self._mainLog.write('<tr><th>No support</th>'
                            '<td>%d (%d%%)</td></tr>\n' %
                            (noSupportCount,
                             round(100 * noSupportCount / float(totalCount))))
        self._mainLog.write('<tr><th>New</th>'
                            '<td>%d (%d%%)</td></tr>\n' %
                            (newCount,
                             round(100 * newCount / float(totalCount))))
        self._mainLog.write('<tr><th>Regressions</th>'
                            '<td>%d (%d%%)</td></tr>\n' %
                            (regressionCount,
                             round(100 * regressionCount /
                                   float(totalCount))))

        self._mainLog.write("</table>\n")
        self._mainLog.write("</body></html>\n")

    def okCount(self):
        return self._results.values().count(self.OK)

    def failCount(self):
        return self._results.values().count(self.FAIL)

    def noSupportCount(self):
        return self._results.values().count(self.NO_SUPPORT)

    def okSet(self):
        return set([uri for (uri, r) in self._results.items()
                    if r == self.OK])

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

    # Get model base
    try:
        baseType, baseArgs = parseCmdLineArgs(argv, 'model base')
        modelBase = relrdf.getModelBase(baseType, **baseArgs)
    except InstantiationError, e:
        print >> sys.stderr, ("error: %s") % e
        sys.exit(1)

    # Open test context
    ctx = TestContext(modelBase, manifest.source, 'report', refSet)

    ctx.start()

    # Execute test cases
    successCount = manifest.execute(ctx)

    ctx.end(len(refSet))

    # Write log
    refFile = open(TEST_LOG, "w")
    refFile.writelines([s + '\n' for s in ctx.okSet()])
    refFile.close()
    print "Successful test cases were written to " + TEST_LOG + "\n"
