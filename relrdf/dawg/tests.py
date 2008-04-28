
import ns
from result import SelectQueryResult, ConstructQueryResult

from relrdf import error
from relrdf.sparql import environment
from relrdf.modelimport.rdflibparse import RdfLibParser

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
        
    def execute(self, model, sink):

        print "Running %s..." % self.name,
        
        # Read the action data (SPARQL)
        try:
            query = readFileFromURL(self.action) 
        except IOError, detail:
            print "Failed (%s)" % detail
            return False
        
        try:
            
            # Invoke the parser
            env = environment.ParseEnvironment()
            env.parse(query, self.action)
            
        except Exception, detail:
            if self.expectSuccess:
                print "Failed (%s)" % detail
                return False
            else:
                print "Ok"
                return True;
        
        if self.expectSuccess:
            print "Ok"
            return True
        else:
            print "Failed (Negative test: Expected a parser error)"
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
        
    def evaluate(self, model, sink):

        # Read query
        try:
            query = readFileFromURL(self.query)
        except IOError, detail:
            raise QueryException("Failed to read query", detail)

        # Data to read?
        if self.data != None:
            
            # Create parser
            from relrdf.modelimport.rdflibparse import RdfLibParser
            parser = RdfLibParser("n3")
            
            # Copy data into database (no commit!)
            try:
                parser.parse(self.data, sink)
                sink.finish()
            except Exception, detail:
                sink.rollback()
                raise QueryException("Failed to import data", detail)
        
        # Execute the query
        try:
            # Try to execute the query, always rollback immediately
            try:
                result = model.query('SPARQL', query, self.query)
            finally:
                sink.rollback()
        except Exception, detail:
            raise QueryException("Failed to run query", detail)
        
        return result
        
class SelectQueryEvaluationTest(QueryEvaluationTest):
    
    def __init__(self, uri, triples):        
        super(SelectQueryEvaluationTest, self).__init__(uri, triples)
    
    def execute(self, model, sink):
        
        print "Running %s..." % self.name,
        
        # Read the expected result
        try:
            
            expectedResult = SelectQueryResult(unprefixFileURL(self.result))
            
        except Exception, detail:
            print "Failed to read expected result (%s)" % detail
            return False
        
        # Evaluate the query
        try:
            result = self.evaluate(model, sink)
        except QueryException, detail:
            print "%s (%s)" % (detail.msg, detail.nested)
            return False
    
        # Compare result
        (success, msg) = expectedResult.compare(result)
        if not success:
            print "Failed result match (%s)" % msg
            return False
        
        print "Ok"
        return True

class ConstructQueryEvaluationTest(QueryEvaluationTest):

    def __init__(self, uri, triples):        
        super(ConstructQueryEvaluationTest, self).__init__(uri, triples)

    def execute(self, model, sink):
        print "Running %s..." % self.name,
        
        # Read the expected result
        try:
                        
            expectedResult = ConstructQueryResult(unprefixFileURL(self.result))
            
        except Exception, detail:
            print "Failed to read expected result (%s)" % detail
            return False        
        
        # Evaluate the query
        try:
            result = self.evaluate(model, sink)
        except QueryException, detail:
            print "%s (%s)" % (detail.msg, detail.nested)
            return False
    
        # Compare result
        (success, msg) = expectedResult.compare(result)
        if not success:
            print "Failed result match (%s)" % msg
            return False
                
        print "Ok"
        return True
    
class AskQueryEvaluationTest(QueryEvaluationTest):

    def __init__(self, uri, triples):        
        super(AskQueryEvaluationTest, self).__init__(uri, triples)

    def execute(self, model, sink):
        print "Running %s..." % self.name,
        print "Not implemented yet!"
        return False
