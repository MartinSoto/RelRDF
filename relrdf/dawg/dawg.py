
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
        
        # Initialiase slots
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
    
    def execute(self, model, sink, okSet, log):
        
        if len(self.entries) > 0:
            print "== Executing test cases from %s..." % self.source
            log.manifestStart(self.source)            
        
        cnt = 0
        for entry in self.entries:
            result = entry.execute(model, sink, log)
            if result:
                cnt += 1
                okSet.add(entry.uri)
            
        for manifest in self.manifests:
            cnt += manifest.execute(model, sink, okSet, log)
            
        return cnt
    
class TestLogFile(object):
    
    __slots__ = ('file')
    
    def __init__(self, file):
        self.file = file
    
    def _wrap(self, text):
        return "\n".join(["\n    ".join(textwrap.wrap(t, 100)) for t in text.split("\n")])
    
    def start(self):
        self.file.write("<html><body>\n")
    
    def manifestStart(self, source):
        self.file.write("<h1>Test cases from %s</h1>\n" % source)    
        
    def testStart(self, name, testType):
        self.file.write("<h2>Case %s</h2>\n" % name)
        self.file.write('<table border="1">\n');
        self.testEntry("Type", testType)
    
    def testEntry(self, name, value, pre=False, src=None):
        if not isinstance(value, unicode):
            value = unicode(value, errors='ignore')
        if pre:
            text = value.encode('latin-1').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            value = "<pre>%s</pre>" % self._wrap(text)
        if not src is None:
            value += '<p>(<a href="%s">%s</a>)</p>' % (src, src)
        self.file.write('<tr><th style="vertical-align:top">%s:</th><td>%s</td></tr>' % (name, value))      
        
    def testOk(self, value=""):
        if not isinstance(value, unicode):
            value = unicode(value, errors='ignore')
        self.file.write('<tr><th style="color:green;vertical-align:top">OK</th><td>%s</td></tr>' % (value))  
        self.testEnd()
 
    def testFail(self, value):
        if not isinstance(value, unicode):
            value = unicode(value, errors='ignore')
        self.file.write('<tr><th style="color:red;vertical-align:top">Fail</th><td>%s</td></tr>' % (value))  
        self.testEnd()
        
    def testFailExc(self, msg=None):
        str = ""
        if not msg is None:
            str = "<p>%s:</p>" % msg
        str += "<pre>%s</pre>" % self._wrap(format_exc(1000))
        self.testFail(str)
               
    def testEnd(self, ):
        self.file.write("</table>\n")
    
    def end(self):
        self.file.write("</body></html>\n")

if __name__ == '__main__':
    
    TEST_LOG = 'test.log'
    
    # Command line help
    if len(sys.argv) < 4:
        print "Usage: python dawg.py manifesto.n3 (ref.lst) " \
            ":<model base type> " \
            " [<model base params>] :<model type> [<model params>]" \
            " :<sink type> [<sink params>]"
            
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
        except IOError:
            pass

    # Get model base and sink    
    try:
        baseType, baseArgs = parseCmdLineArgs(argv, 'model base')
        modelBase = relrdf.getModelBase(baseType, **baseArgs)
        
        sinkType, sinkArgs = parseCmdLineArgs(argv, 'sink')
        sink = modelBase.getSink(sinkType, **sinkArgs)
    
        modelType, modelArgs = parseCmdLineArgs(argv, 'model')
        model = modelBase.getModel(modelType, **modelArgs)
        
        # Hack!
        model._connection = sink.connection
            
    except InstantiationError, e:
        print >> sys.stderr, ("error: %s") % e
        sys.exit(1)
        
    # Open test log
    log = TestLogFile(open("log.html", "w"))
        
    # Execute test cases
    okSet = set()
    successCount = manifest.execute(model, sink, okSet, log)
    
    # Compare with reference set
    refSuccessCount = 0
    for test in refSet:
        if test in okSet:
            refSuccessCount = refSuccessCount + 1

    print "== %d/%d test cases succeeded!" % (successCount, entryCount)
    if len(refSet) != 0:
        print "== (%d/%d from reference set)" % (refSuccessCount, len(refSet))
    
    log.end()
    
    # Write log
    refFile = open(TEST_LOG, "w")
    refFile.writelines([s + '\n' for s in okSet])
    refFile.close()
    print "Successful test cases were written to " + TEST_LOG + "\n"
    
    