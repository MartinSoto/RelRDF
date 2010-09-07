# -*- coding: utf-8 -*-
# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2010 Fraunhofer-Institut fuer Experimentelles
#                         Software Engineering (IESE).
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


from relrdf.localization import _

from error import InstantiationError, ConfigurationError
import cmdline


def _getModule(modelbaseType):
    """Retrieve the Python module associated to a particular modelbase
    type.
    """
    modelbaseTypeNorm = modelbaseType.lower()

    # This is implemented this way in order to import only the modules
    # that are requested.
    if modelbaseTypeNorm == "postgres":
        from db import postgres
        return postgres
    elif modelbaseTypeNorm == "debug":
        import debug
        return debug
    else:
        raise InstantiationError("invalid model base type '%s'"
                                 % modelbaseType)

def getModelbase(mbConf):
    module = _getModule(mbConf.name)
    return module.getModelbase(mbConf)

def getModelbaseFromParams(mbType, **mbParams):
    """A convenience function to create a modelbase directly from its
    parameters, passed as keywords.

    This function creates a configuration object and passes it to
    func:`getModelbase`.
    """
    mbConfCls = getConfigClass((mbType,))
    mbConf = mbConfCls.fromUnchecked(**mbParams)
    return getModelbase(mbConf)

def getConfigClass(path):
    try:
        module = _getModule(path[0])
    except InstantiationError, e:
        raise ConfigurationError(unicode(e))

    return module.getConfigClass(path[1:])

def getCmdLineObject(path):
    try:
        module = _getModule(path[0])
    except InstantiationError, e:
        raise ConfigurationError(unicode(e))

    return module.getCmdLineObject(path[1:])

def getModelbases():
    import db.mysql
    return {"postgres": db.postgres.modelbase.Modelbase}
