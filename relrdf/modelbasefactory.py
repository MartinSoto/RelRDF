# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2010 Fraunhofer-Institut fuer Experimentelles
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


from relrdf.localization import _

from error import InstantiationError, ConfigurationError
import cmdline


def _getModule(modelBaseType):
    """Retrieve the Python module associated to a particular modelbase
    type.
    """
    modelBaseTypeNorm = modelBaseType.lower()

    if modelBaseTypeNorm == "postgres":
        from db import postgres
        return postgres
    elif modelBaseTypeNorm == "debug":
        import debug
        return debug
    else:
        raise InstantiationError("invalid model base type '%s'"
                                 % modelBaseType)

def getModelBase(modelBaseType, **modelBaseArgs):
    module = _getModule(modelBaseType)

    # This is implemented this way in order to import only the modules
    # that are requested.

    try:
        return module.getModelBase(**modelBaseArgs)
    except TypeError, e:
        raise InstantiationError(
            _("Missing or invalid model base arguments: %s") % e)

def getConfigClass(path):
    # This is implemented this way in order to import only the modules
    # that are requested.

    try:
        module = _getModule(path[0])
    except InstantiationError, e:
        raise ConfigurationError(str(e))

    return module.getConfigClass(path[1:])

def getModelBases():
    import db.mysql
    return {"postgres": db.postgres.modelbase.ModelBase}
