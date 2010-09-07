# -*- coding: utf-8 -*-
# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2010      Martín Soto
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

"""Base classes for RelRDF's modelbase and model objects"""

from relrdf import centralfactory


class Modelbase(object):
    """Base class for the RelRDF modelbases."""

    __slots__ = ()

    name = None
    """Modelbase name."""

    def getModel(self, mbConf):
        raise NotImplementedError

    def getModelFromParams(self, modelType, **modelParams):
        """A convenience method to create a model directly from its
        parameters, passed as keywords.

        This method creates a configuration object and passes it to
        method:`getModel`.
        """
        modelConfCls = centralfactory.getConfigClass((self.name, modelType))
        modelConf = modelConfCls.fromUnchecked(**modelParams)
        return self.getModel(modelConf)

    def getSink(self, modelConf):
        raise NotImplementedError

    def getSinkFromParams(self, sinkType, **sinkParams):
        """A convenience method to create a sink directly from its
        parameters, passed as keywords.

        This method creates a configuration object and passes it to
        method:`getSink`.
        """
        sinkConfCls = centralfactory.getConfigClass((self.name, sinkType))
        sinkConf = sinkConfCls.fromUnchecked(**sinkParams)
        return self.getSink(sinkConf)

    def commit(self):
        pass

    def close(self):
        pass


class Model(object):
    """Base class for the RelRDF models."""

    __slots__ = ()


class Sink(object):
    """Base class for the RelRDF statement sinks."""

    __slots__ = ()

    def triple(self, subject, pred, object):
        raise NotImplementedError

    def close(self):
        pass
