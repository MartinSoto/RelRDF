import sys

import MySQLdb

import rdfxmlparse


class DbRdfSink(object):
    __slots__ = ('cursor',
                 'versionId')

    def __init__(self, cursor, versionId):
        self.cursor = cursor
        self.versionId = versionId

    def triple(self, subject, pred, objectType, object):
        cursor.execute(
            """
            INSERT INTO data_types (uri)
            VALUES (%s)
            ON DUPLICATE KEY UPDATE uri = uri""",
            (objectType))
        cursor.execute(
            """
            INSERT INTO statements (subject, predicate, object_type, object)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE subject = subject""",
            (subject, pred, self.cursor.lastrowid, object))
        cursor.execute(
            """
            INSERT INTO version_statement (version_id, stmt_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE version_id = version_id""",
            (self.versionId, self.cursor.lastrowid))


conn = MySQLdb.connect(host='localhost', passwd="d0nZknut", db="rdf")
cursor = conn.cursor()

rdfxmlparse.parseURI(sys.argv[1], sink=DbRdfSink(cursor, int(sys.argv[2])))

cursor.close()
