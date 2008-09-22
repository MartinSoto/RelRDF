
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
        
    def execute(self, model, sink, ref, log):

        print "Running %s..." % self.name,

        # Create log        
        if self.expectSuccess:
            log.testStart(self.name, "Syntax test (positive)")
        else:
            log.testStart(self.name, "Syntax test (negative)")
        
        # Read the action data (SPARQL)
        try:
            query = readFileFromURL(self.action) 
            log.testEntry("Query", query, pre=True, src=self.action)
        except IOError, detail:
            print "Failed (%s)" % detail
            log.testFailExc(ref, "Could not read query")
            return False
        
        try:
            
            # Invoke the parser
            env = environment.ParseEnvironment()
            env.parse(query, self.action)
            
        except Exception, detail:
            if self.expectSuccess:
                print "Failed (%s)" % detail
                log.testFailExc(ref, "Could not parse query")
                return False
            else:
                print "Ok"
                log.testOk(ref)
                return True;
        
        if self.expectSuccess:
            print "Ok"
            log.testOk(ref)
            return True
        else:
            print "Failed (Negative test: Expected a parser error)"
            log.testFail(ref, "Negative test: Expected a parser error")
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
                 'type',
                 'query',
                 'data',
                 'result'  
                 )
    
    def __init__(self, uri, triples):
        
        self.uri = uri
        self.name = triples.get((uri, ns.mf.name))
        self.type = triples.get((uri, ns.rdf.type))        
        
        action = triples.get((uri, ns.mf.action))
        self.query = triples.get((action, ns.qt.query))
        self.data = triples.get((action, ns.qt.data))
        
        self.result = triples.get((uri, ns.mf.result))
        
    def evaluate(self, model, sink, ref, log):

        # Read query
        try:
            query = readFileFromURL(self.query)
            log.testEntry("Query", query, pre=True, src=self.query)
        except IOError, detail:
            log.testFailExc(ref, "Failed to read query")
            raise QueryException("Failed to read query", detail)

        # Data to read?
        if self.data != None:
            
            # Read text for log
            dataText = readFileFromURL(self.data)
            log.testEntry("Data", dataText, pre=True, src=self.data)

            # Create parser
            from relrdf.modelimport.redlandparse import RedlandParser
            parser = RedlandParser("turtle")
                        
            # Copy data into database (no commit!)
            try:
                parser.parse(self.data, sink)
                sink.finish()
            except Exception, detail:
                sink.rollback()
                log.testFailExc(ref, "Failed to import data")
                raise QueryException("Failed to import data", detail)
        
        # Execute the query
        try:
            
            try:
                
                # Parse query, log SQL
                sql = model.querySQL('SPARQL', query, self.query)
                log.testEntry("SQL", sql, pre=True)
                
                # Try to execute the query
                result = model.query('SPARQL', query, self.query)
                
            finally:
                
                # Always rollback immediately
                sink.rollback()
                
        except Exception, detail:
            log.testFailExc(ref, "Failed to run query")
            raise QueryException("Failed to run query", detail)
        
        return result
        
class SelectQueryEvaluationTest(QueryEvaluationTest):
    
    def __init__(self, uri, triples):        
        super(SelectQueryEvaluationTest, self).__init__(uri, triples)
    
    def execute(self, model, sink, ref, log):
        
        print "Running %s..." % self.name,
        log.testStart(self.name, "Select query test")
        
        # Read the expected result
        try:
                        
            # Read text for log
            log.testEntry("Expected", "", src=self.result)
            
            expectedResult = SelectQueryResult(unprefixFileURL(self.result))
            
        except Exception, detail:
            log.testFailExc(ref, "Failed to read expected result")
            print "Failed to read expected result (%s)" % detail
            return False
        
        # Evaluate the query
        try:
            result = self.evaluate(model, sink, ref, log)
        except QueryException, detail:
            print "%s (%s)" % (detail.msg, detail.nested)
            return False
    
        # Compare result
        (success, msg) = expectedResult.compare(result, log)
        if not success:
            log.testFail(ref, "Failed result match (%s)" % msg)
            print "Failed result match (%s)" % msg
            return False
        
        log.testOk(ref)        
        print "Ok"
        return True

class ConstructQueryEvaluationTest(QueryEvaluationTest):

    def __init__(self, uri, triples):        
        super(ConstructQueryEvaluationTest, self).__init__(uri, triples)

    def execute(self, model, sink, ref, log):
        print "Running %s..." % self.name,
        log.testStart(self.name, "Construct query test")
        
        # Read the expected result
        try:
                        
            log.testEntry("Expected", "", src=self.result)

            expectedResult = ConstructQueryResult(unprefixFileURL(self.result))
                        
        except Exception, detail:
            log.testFailExc(ref, "Failed to read expected result")
            print "Failed to read expected result (%s)" % detail
            return False        
        
        # Evaluate the query
        try:
            result = self.evaluate(model, sink, ref, log)
        except QueryException, detail:
            print "%s (%s)" % (detail.msg, detail.nested)
            return False
    
        # Compare result
        (success, msg) = expectedResult.compare(result)
        if not success:
            log.testFail(ref, "Failed result match (%s)" % msg)
            print "Failed result match (%s)" % msg
            return False
        
        log.testOk(ref)
        print "Ok"
        return True
    
class AskQueryEvaluationTest(QueryEvaluationTest):

    def __init__(self, uri, triples):        
        super(AskQueryEvaluationTest, self).__init__(uri, triples)

    def execute(self, model, sink, ref, log):
        print "Running %s..." % self.name,
        print "Not implemented yet!"
        return False
