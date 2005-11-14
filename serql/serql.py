import sys

import antlr

import query


class Parser(antlr.LLkParser):
   def __init__(self, *args, **kwargs):
      super(Parser, self).__init__(*args, **kwargs)

      try:
         self.query = kwargs['query']
      except KeyError:
         self.query = query.Query()

      # Set the standard SerQL predefined prefixes.
      self.query.setPrefix('rdf',
                           'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
      self.query.setPrefix('rdfs',
                           'http://www.w3.org/2000/01/rdf-schema#')
      self.query.setPrefix('xsd',
                           'http://www.w3.org/2001/XMLSchema#')
      self.query.setPrefix('owl',
                           'http://www.w3.org/2002/07/owl#')
      self.query.setPrefix('serql',
                           'http://www.openrdf.org/schema/serql#')

      @staticmethod
      def makePatterns(nodeList1, edge, nodeList2):
         patterns = []
         for n1 in nodeList1:
            for n2 in nodeList2:
               patterns.append(query.Pattern(n1, edge, n2))

         return patterns

