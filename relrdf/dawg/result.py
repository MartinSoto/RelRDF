
import ns

from relrdf.expression import uri, literal

from relrdf.modelimport.redlandparse import RedlandParser
from relrdf.modelimport.rdfxmlparse import RdfXmlParser

from relrdf.basesinks import ListSink, DictSink

from xml.dom.minidom import parse

import pprint

# Helpers for XML parsing
def getTextContent(node):
    if node.nodeType == node.TEXT_NODE:
        return node.nodeValue
    else:
        result = ""        
        for child in node.childNodes:
            result += getTextContent(child)
        return result            
    
def getAttributeNone(parent, name):
    if parent.hasAttribute(name):
        return parent.getAttribute(name)
    else:
        return None

# Helpers: Create a parser by file extension
def getFileExtension(file):
    exts = file.rsplit('.', 1)
    if len(exts) < 2:
        return ""
    else:
        return exts[1]

class QueryResultException(Exception):
    pass

def _get(dict, idx):
    try:
        return dict[idx]
    except KeyError:
        return None

def _compare(cols, rows1, rows2, idx2, i=0, blankMap={}):
    
    # Finished?
    if i >= len(rows1):
        if len(rows2) == 0:
            return True, "Ok"
        else:
            return False, "Could not match expected result row %s!" % rows2[0]
    
    # Get row to match
    row1 = rows1[i]
    
    # Search match
    failmsg = None
    for j, row2 in enumerate(rows2):
        
        # Match all variables
        curBlankMap = blankMap.copy()
        match = True
        blankNodes = False
        for var in cols:
            if uri.isBlank(row1[var]) and uri.isBlank(row2[var]):
                blankNodes = True
                if curBlankMap.get(row1[var]) == None:
                    curBlankMap[row1[var]] = row2[var]
                    continue
                elif curBlankMap[row1[var]] == row2[var]:
                    continue
                else:
                    match = False
                    break                                
            elif _get(row1, var) != _get(row2, var):
                match = False
                break
        
        if not match:
            continue
        
        # Index mismatch?
        if j < len(idx2) and idx2[j] != i+1:
            failmsg = "Matching expected result row %s has wrong index (%d != %d)!" % (unicode(row1), idx2[j], i+1)
            continue
        
        # Recursively match
        rows2_ = rows2[:j] + rows2[j+1:]
        idx2_ = idx2[:j] + idx2[j+1:]
        result, failmsg = _compare(cols, rows1, rows2_, idx2_, i+1, curBlankMap)
        if result:
            return True, "Ok"
        
        # If there are no blank nodes, no other row can match
        if not blankNodes:
            return False, failmsg
    
    # Generate error message
    if failmsg == None:
        failmsg = "Could not match result row %s!" % unicode(row1)
    
    # No match => backtrack
    return False, failmsg
    
class SelectQueryResult:

    __slots__ = ('variables',
                 'results',
                 'indexes',
                 
                 'blanks'
                 )
    
    def __init__(self, file):

        # Initialize
        self.variables = []
        self.results = []
        self.indexes = []
        
        self.blanks = {}
        
        # guess format by extension
        ext = getFileExtension(file)
        if ext == 'srx':
            self.parseXML(file)
        elif ext == 'ttl':
            self.parseTriples(file, RedlandParser(format='turtle'))
        elif ext == 'rdf':
            self.parseTriples(file, RdfXmlParser())
        else:
            raise QueryResultException(), "invalid file extension for select query result: %d" % ext
        
    def parseXML(self, file):
        
        # Parse the result file
        doc = parse(file)
        
        # Get variables
        headElem = doc.getElementsByTagName("head")[0]
        for varElem in headElem.getElementsByTagName("variable"):            
            self.variables.append(varElem.getAttribute("name"))
            
        # Get results
        resultsElem = doc.getElementsByTagName("results")[0]
        for resultElem in resultsElem.getElementsByTagName("result"):
            result = {}
            for bindElem in resultElem.getElementsByTagName("binding"):
                
                # Get actual value (might be one of the following types)
                val = None
                for valElem in bindElem.getElementsByTagName("uri"):
                    val = uri.Uri(getTextContent(valElem))
                for valElem in bindElem.getElementsByTagName("literal"):
                    lang = getAttributeNone(valElem, "lang")
                    dt = getAttributeNone(valElem, "datatype")
                    val = literal.Literal(getTextContent(valElem), lang, dt)
                for valElem in bindElem.getElementsByTagName("bnode"):
                    label = getTextContent(valElem)
                    try:
                        val = self.blanks[label]
                    except KeyError:
                        val = uri.newBlank()
                        self.blanks[label] = val
                    
                # Put into map
                name = bindElem.getAttribute("name")
                result[name] = val
        
            # Add result row
            self.results.append(result)
            
    def parseTriples(self, file, parser):
        
        # Parse into list
        triples = ListSink()
        parser.parse(file, triples)
        
        # Copy contents to dict sink for convenience
        dict = DictSink()
        for triple in triples:
            dict.triple(*triple)
            
        # Get variables
        root = None
        for subject, pred, object in triples:            
            if pred == uri.Uri(ns.rs.resultVariable) and isinstance(object, literal.Literal):
                root = subject
                self.variables.append(object)
        
        # Get solutions
        for subject, pred, object in triples:
            if subject != root or pred != uri.Uri(ns.rs.solution):
                continue
            
            # Has an index?
            index = dict.get((object, ns.rs["index"]))
            if isinstance(index, literal.Literal) and len(self.results) == len(self.indexes):
                self.indexes.append(int(index))
            
            # Get bindings
            result = { }
            for subject2, pred2, object2 in triples:
                if subject2 != object or pred2 != uri.Uri(ns.rs.binding):
                    continue
                name = dict[object2, ns.rs.variable]
                val = dict[object2, ns.rs.value]
                result[name] = val
                                    
            # Add result row
            self.results.append(result)
    
    def compare(self, result, log):
        
        resultVars = result.columnNames
    
        # Compare variables
        for var in self.variables:
            if not var in resultVars:
                return False, "Variable %s not in result!" % var
        for var in resultVars:
            if not var in self.variables:
                return False, "Unexpected variable %s in result!" % var
        
        # Convert result into dictionary list
        resultList = []
        for row in result:
            
            # Convert to dictionary
            rowd = {}
            for var, val in zip(resultVars, row):
                rowd[var] = val
            
            # Add to list
            resultList.append(rowd)
            
        log.testEntry('Result', pprint.pformat(resultList))
        log.testEntry('Expected', pprint.pformat(self.results))
        
        # Compare lists
        return _compare(self.variables, resultList, self.results, self.indexes)
                
class ConstructQueryResult:
    
    __slots__ = ('triples')
    
    def __init__(self, file):
                
        # Create praser by extension
        ext = getFileExtension(file)
        if ext == 'ttl':
            parser = RedlandParser(format='turtle')
        elif ext == 'rdf':
            parser = RdfXmlParser()
        else:
            raise QueryResultException(), "invalid file extension for construct query result: %d" % ext
        
        # Create list sink, parse result
        self.triples = ListSink()
        parser.parse(file, self.triples)
        
    def compare(self, result):
        
        # Convert result to list
        resultList = []
        for triple in result:
            resultList.append((triple[0], triple[1], triple[2]))
        
        # Compare the results
        return _compare([0,1,2], resultList, self.triples, [])
    
