
import ns
from result import SelectQueryResult, ConstructQueryResult

from relrdf import error
from relrdf.sparql import environment
from relrdf.modelimport.rdflibparse import RdfLibParser

import pprint

def unprefixFileURL(url):
    
    # File name of action (must be a file URL)
    PREFIX="file://"
    if not url.startswith(PREFIX):
        raise IOError, "Invalid URI: Only file URIs supported!"
    return url[len(PREFIX):]
    
def readFileFromURL(fileName):

    # Read the file
    f = file(unprefixFileURL(fileName), "rb")
    data = f.read()
    f.close()

    return data    
        
class SyntaxTest(object):
    
    __slots__ = ('uri',
                 'name',
                 'type',
                 'action',
                 'expectSuccess'
                 )
    
    def __init__(self, uri, triples, expectSuccess):
        
        self.uri = uri
        self.name = triples.get((uri, ns.mf.name))
        self.type = triples.get((uri, ns.rdf.type))
        self.action = triples.get((uri, ns.mf.action))
        self.expectSuccess = expectSuccess
        
    def execute(self, ctx):

        print "Running %s..." % self.name,

        # Create log        
        if self.expectSuccess:
            ctx.testStart(self.uri, self.name, "Syntax test (positive)")
        else:
            ctx.testStart(self.uri, self.name, "Syntax test (negative)")
        
        # Read the action data (SPARQL)
        try:
            query = readFileFromURL(self.action) 
            ctx.testEntry("Query", query, pre=True, src=self.action)
        except IOError, detail:
            print "Failed (%s)" % detail
            ctx.testFailExc("Could not read query")
            return False
        
        try:
            
            # Invoke the parser
            env = environment.ParseEnvironment()
            env.parse(query, self.action)
            
        except Exception, detail:
            if self.expectSuccess:
                print "Failed (%s)" % detail
                if not isinstance(detail, error.NotSupportedError):
                    ctx.testFailExc("Could not parse query")
                else:
                    ctx.testNoSupport("Could not parse query")
                return False
            else:
                print "Ok"
                ctx.testOk()
                return True;
        
        if self.expectSuccess:
            print "Ok"
            ctx.testOk()
            return True
        else:
            print "Failed (Negative test: Expected a parser error)"
            ctx.testFail("Negative test: Expected a parser error")
            return True

class QueryException(Exception):
    
    __slots__ = ('msg',
                 'nested',
                 )
    
    def __init__(self, msg, nested):
        self.msg = msg
        self.nested = nested

class QueryEvaluationTest(object):
    
    __slots__ = ('uri',
                 'name',
                 'comment',
                 'type',
                 'query',
                 'data', 'graphData',
                 'result'  
                 )
    
    def __init__(self, uri, triples):
        
        self.uri = uri
        self.name = triples.get((uri, ns.mf.name))
        self.comment = triples.get((uri, ns.rdfs.comment))
        self.type = triples.get((uri, ns.rdf.type))        
        
        action = triples.get((uri, ns.mf.action))
        self.query = triples.get((action, ns.qt.query))
        self.data = triples.get((action, ns.qt.data))
        self.graphData = triples.get((action, ns.qt.graphData))
        
        self.result = triples.get((uri, ns.mf.result))
        
    def _readData(self, ctx, uri, caption, asGraph):
        
        # Copy text into log
        dataText = readFileFromURL(uri)
        ctx.testEntry(caption, dataText, pre=True, src=uri)

        # Create parser
        from relrdf.modelimport.redlandparse import RedlandParser
        parser = RedlandParser("turtle")
        
        # Set graph
        if asGraph:
            ctx.sink.setGraph(uri)
        
        # Copy data into database (no commit!)
        try:
            parser.parse(self.data, ctx.sink)
            sink.finish()
        except Exception, detail:
            ctx.testFailExc("Failed to import data")
            raise QueryException("Failed to import data", detail)        
        
    def _readData(self, ctx, uri, caption, asGraph):
        
        # Copy text into log
        dataText = readFileFromURL(uri)
        ctx.testEntry(caption, dataText, pre=True, src=uri)

        # Create parser
        from relrdf.modelimport.redlandparse import RedlandParser
        parser = RedlandParser("turtle")
        
        # Set graph
        if asGraph:
            ctx.sink.setGraph(uri)
        
        # Copy data into database (no commit!)
        try:
            parser.parse(uri, ctx.sink)
            ctx.sink.finish()
        except Exception, detail:
            ctx.testFailExc("Failed to import data")
            raise QueryException("Failed to import data", detail)
                    
    def evaluate(self, ctx):

        # Read query
        try:
            query = readFileFromURL(self.query)
            ctx.testEntry("Query", query, pre=True, src=self.query)
        except IOError, detail:
            ctx.testFailExc(ref, "Failed to read query")
            raise QueryException("Failed to read query", detail)

        # Data to read?
        if self.data is not None:
            self._readData(ctx, self.data, "Data", False)
        if self.graphData is not None:
            self._readData(ctx, self.graphData, "Graph Data", True)
                    
        # Execute the query
        try:
            
            # Parse query, log SQL
            sql = ctx.model.querySQL('SPARQL', query, self.query)
            ctx.testEntry("SQL", sql, pre=True)
            
            # Try to execute the query
            result = ctx.model.query('SPARQL', query, self.query)                
                
        except Exception, detail:
            if not isinstance(detail, error.NotSupportedError):
                ctx.testFailExc("Failed to run query")
            else:
                ctx.testNoSupport("Failed to run query")
            raise QueryException("Failed to run query", detail)
        
        return result
        
class SelectQueryEvaluationTest(QueryEvaluationTest):
    
    def __init__(self, uri, triples):        
        super(SelectQueryEvaluationTest, self).__init__(uri, triples)
    
    def execute(self, ctx):
        
        print "Running %s..." % self.name,
        ctx.testStart(self.uri, self.name, "Select query test")
        if not self.comment is None:
            ctx.testEntry("Comment", self.comment)
        
        # Read the expected result
        try:
                        
            # Read text for log
            ctx.testEntry("Expected", "", src=self.result)
            
            expectedResult = SelectQueryResult(unprefixFileURL(self.result))
            
        except Exception, detail:
            ctx.testFailExc("Failed to read expected result")
            print "Failed to read expected result (%s)" % detail
            return False
        
        # Evaluate the query
        try:
            result = self.evaluate(ctx)
        except QueryException, detail:
            print "%s (%s)" % (detail.msg, detail.nested)
            return False
    
        # Compare result
        (success, msg) = expectedResult.compare(result, ctx)
        if not success:
            ctx.testFail("Failed result match (%s)" % msg)
            print "Failed result match (%s)" % msg
            return False
        
        # Okay        
        ctx.testOk()
        print "Ok"
        return True

class ConstructQueryEvaluationTest(QueryEvaluationTest):

    def __init__(self, uri, triples):        
        super(ConstructQueryEvaluationTest, self).__init__(uri, triples)

    def execute(self, ctx):
        print "Running %s..." % self.name,
        ctx.testStart(self.uri, self.name, "Construct query test")
        if not self.comment is None:
            ctx.testEntry("Comment", self.comment)
        
        # Read the expected result
        try:
                        
            ctx.testEntry("Expected", "", src=self.result)

            expectedResult = ConstructQueryResult(unprefixFileURL(self.result))
                        
        except Exception, detail:
            ctx.testFailExc(ref, "Failed to read expected result")
            print "Failed to read expected result (%s)" % detail
            return False    
        
         # Evaluate the query
        try:
            result = self.evaluate(ctx)
        except QueryException, detail:
            print "%s (%s)" % (detail.msg, detail.nested)
            return False
    
        # Compare result
        (success, msg) = expectedResult.compare(result)
        if not success:
            ctx.testFail("Failed result match (%s)" % msg)
            print "Failed result match (%s)" % msg
            return False
        
        # Okay        
        ctx.testOk()
        print "Ok"
        return True
    
class AskQueryEvaluationTest(QueryEvaluationTest):

    def __init__(self, uri, triples):        
        super(AskQueryEvaluationTest, self).__init__(uri, triples)

    def execute(self, ctx):
        print "Running %s..." % self.name,
        print "Not implemented yet!"
        ctx.testStart(self.uri, self.name, "Construct query test")        
        ctx.testNoSupport()        
        return False
