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


from relrdf.error import InstantiationError

class SingleGraphRdfSink(object):
    """An RDF sink that sends all tuples to a single graph in the
    database."""

    __slots__ = ('modelbase',
                 'baseGraph',
                 'verbose',
                 'delete',
                 'graphId',)

    def __init__(self, modelbase, baseGraph, verbose=False, delete=False):
        self.modelbase = modelbase
        self.baseGraph = baseGraph
        self.verbose = verbose
        self.delete = delete

        self.setGraph(self.baseGraph)

    def setGraph(self, graphUri):
        """ Sets the name of the graph to receive triples."""
        # Get graph ID from database
        self.graphId = int(self.modelbase.lookupGraphId(graphUri,
                                                        create=True))

    def triple(self, subject, pred, object):
        self.modelbase.queueTriple(self.graphId, self.delete, subject,
                                   pred, object)

    def close(self):
        self.modelbase = None


_sinkFactories = {
    'singlegraph': SingleGraphRdfSink,
    }

def getSink(modelbase, sinkType, **sinkArgs):
    sinkTypeNorm = sinkType.lower()

    try:
        return _sinkFactories[sinkTypeNorm](modelbase, **sinkArgs)
    except KeyError:
        raise InstantiationError(("Invalid sink type '%s'") % sinkType)
    except TypeError, e:
        raise InstantiationError(("Missing or invalid sink arguments: %s") %
                                 e)
