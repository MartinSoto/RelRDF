# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2009 Fraunhofer-Institut fuer Experimentelles
#                         Software Engineering (IESE).
#
# RelRDF is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA. 


import md5

from relrdf.expression import uri, literal


class SingleVersionRdfSink(object):
    """An RDF sink that sends all tuples to a single model version in
    the database."""

    __slots__ = ('connection',
                 'cursor',
                 'versionId',

                 'pendingRows',
                 'totalRows')

    # Maximum number of rows per insert query.
    ROWS_PER_QUERY = 100

    def __init__(self, connection, versionId):
        self.connection = connection
        self.versionId = versionId

        self.pendingRows = []
        self.totalRows = 0

        self.cursor = self.connection.cursor()

        self.cursor.execute(
            """
            DROP TABLE IF EXISTS statements_temp;
            """)

        self.cursor.execute(
            """
            CREATE TEMPORARY TABLE statements_temp (
              hash binary(16) NOT NULL,
              subject varchar(255) NOT NULL,
              predicate varchar(255) NOT NULL,
              object_type varchar(255) NOT NULL,
              object longtext NOT NULL
            );
            """)

    def triple(self, subject, pred, object):
        if isinstance(object, uri.Uri):
            objectType = '<RESOURCE>'
        elif isinstance(object, literal.Literal):
            if object.typeUri is None:
                objectType = '<LITERAL>'
            else:
                objectType = object.typeUri
        else:
            assert False, "Unexpected object type '%d'" \
                   % object.__class__.__name__

        # Calculate a hash value for the statement.
        m = md5.new()
        m.update(subject.encode('utf-8'))
        m.update(pred.encode('utf-8'))
        m.update(objectType.encode('utf-8'))
        m.update(unicode(object).encode('utf-8'))

        self.pendingRows.append((m.digest(),
                                 unicode(subject).encode('utf-8'),
                                 unicode(pred).encode('utf-8'),
                                 unicode(objectType).encode('utf-8'),
                                 unicode(object).encode('utf-8')))
        if len(self.pendingRows) >= self.ROWS_PER_QUERY:
            self._writePendingRows()
                                
    def _writePendingRows(self):
        if len(self.pendingRows) == 0:
            return

        self.cursor.executemany(
            """
            INSERT INTO statements_temp
              (hash, subject, predicate, object_type, object)
            VALUES (?,?,?,?,?);""",
            self.pendingRows)

        self.totalRows += len(self.pendingRows)
        self.pendingRows = []

    def close(self):
        self._writePendingRows()

        self.cursor.execute("select count(*) from statements_temp;")
        for (count,) in self.cursor:
            print 'Inserted count: %d' % count

        self.cursor.execute(
            """
            INSERT OR IGNORE INTO data_types (uri)
              SELECT s.object_type
              FROM statements_temp s;
            """)
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO statements (hash, subject, predicate,
                                              object_type, object)
              SELECT s.hash, s.subject, s.predicate, dt.id, s.object
              FROM statements_temp s, data_types dt
              WHERE s.object_type = dt.uri;
            """)
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO version_statement (version_id, stmt_id)
              SELECT ? AS v_id, s.id
              FROM statements s, statements_temp st
              WHERE s.hash = st.hash;
            """, (self.versionId,))
        self.cursor.execute(
            """
            DROP TABLE statements_temp;
            """)

        self.cursor.close()
        self.connection.commit()

        print "%d statements written" % self.totalRows


_sinkFactories = {
    'singleversion': SingleVersionRdfSink,
    }

def getSink(connection, sinkType, **sinkArgs):
    sinkTypeNorm = sinkType.lower()

    try:
        return _sinkFactories[sinkTypeNorm](connection, **sinkArgs)
    except KeyError:
        assert False, "Invalid sink type '%s'" % modelType
