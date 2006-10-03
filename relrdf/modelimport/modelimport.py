import sys

import MySQLdb

import relrdf

import rdfxmlparse
import vmodellparse


if len(sys.argv) < 4:
    print >> sys.stderr, \
          'usage: modelimport.py <file type> <uri or file> <host> ' \
          '<database> <sink type> [<sink params>]'
    sys.exit(1)

fileType, uriOrFile, host, db, sinkType = sys.argv[1:6]

sinkParams = {}
for arg in sys.argv[6:]:
    key, value = arg.split('=')
    sinkParams[key] = value

modelBase = relrdf.getModelBase('mysql', host=host, db=db,
                                read_default_group='client')
sink = modelBase.getSink(sinkType, **sinkParams)

fileType = fileType.lower() 

if fileType == 'rdfxml':
    rdfxmlparse.parseFromUri(uriOrFile, sink=sink)
elif fileType in ('v-modell', 'vmodell'):
    vmodellparse.VModellParser(open(uriOrFile), sink=sink)
else:
    error("Invalid file type '%s'" % fileType)

sink.close()
