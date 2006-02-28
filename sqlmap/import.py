import sys

import MySQLdb

import rdfxmlparse
import sinks


(db, uri, versionNumber) = sys.argv[1:]

conn = MySQLdb.connect(host='localhost', db=db, read_default_group='client')
cursor = conn.cursor()

rdfxmlparse.parseFromUri(uri,
                         sink=sinks.VersionRdfSink(cursor,
                                                   int(versionNumber)))

cursor.close()
