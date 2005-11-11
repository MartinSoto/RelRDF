import sys

import antlr

import query


class Parser(antlr.LLkParser):
   def __init__(self,*args):
      super(Parser,self).__init__(*args)

      self.query = query.Query()

