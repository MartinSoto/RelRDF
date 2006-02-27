#!/usr/bin/python

import sys
import string

import RDF

import prefixes


class QueryError(Exception):
    pass


#RDF.debug(1)

# Initialize a global parser.
parser = RDF.Parser('raptor')
if parser is None:
    raise QueryError, "Failed to create RDF.Parser raptor"


def Query(queryString):
    return RDF.Query(queryString + prefixes.using)


class Model(object):
    __slots__ = ('storage',
                 'model')

    def __init__(self, file):
        # Initialize a global Redland storage.
        self.storage = RDF.Storage(storage_name="hashes",
                                   name="test",
                                   options_string="new='yes',"
                                   "hash-type='memory',dir='.'")
        if self.storage is None:
            raise QueryError, "new RDF.Storage failed"

        self.model = RDF.Model(self.storage)
        if self.model is None:
            raise QueryError, "new RDF.model failed"

        uri = RDF.Uri(string = "file:" + file)

        for s in parser.parse_as_stream(uri, uri):
            self.model.add_statement(s)

    def query(self, querySpec):
        if isinstance(querySpec, str):
            query = Query(querySpec)
        else:
            query = querySpec

        return query.execute(self.model)


if __name__ == "__main__":
    file = sys.argv[1]
    querySpec = sys.argv[2]
    resultFields = sys.argv[3:]

    model = Model(file)

    print string.join(resultFields, ',')
    for result in model.query(querySpec):
        print string.join([str(result[field]) for field in resultFields], ',')
