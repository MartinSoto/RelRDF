import sys

import MySQLdb

import rdfxmlparse
import vmodellparse
from sqlmap import VersionRdfSink


def error(msg):
    print >> sys.stderr, "%s: %s" % (sys.argv[0], msg)
    sys.exit(1)

def usage():
    print >> sys.stderr, \
          "Usage: %s <database> <version> <type> <uri or file>" % \
          sys.argv[0]
    sys.exit(1)

try:
    (db, versionNumber, fileType, uriOrFile) = sys.argv[1:]
except:
    usage()

try:
    versionNumber = int(versionNumber)
except:
    error("Version number must be an integer")

fileType = fileType.lower() 

conn = MySQLdb.connect(host='localhost', db=db, read_default_group='client')
cursor = conn.cursor()
sink = VersionRdfSink(cursor, int(versionNumber))

if fileType == 'rdfxml':
    rdfxmlparse.parseFromUri(uriOrFile, sink=sink)
elif fileType in ('v-modell', 'vmodell'):
    vmodellparse.VModellParser(uriOrFile, sink=sink)
else:
    error("Invalid file type '%s'" % fileType)

cursor.close()
