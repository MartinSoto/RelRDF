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

    try:
        return module.getModelBase(**modelBaseArgs)
    except TypeError, e:
        raise InstantiationError(
            _("Missing or invalid model base arguments: %s") % e)

def thawModelbaseConfig(modelBaseType, version, configData):
    """Create a configuration object from serialized ("frozen") data.

    Parameters:

    * `modelBaseType`: A unique identifier for the modelbase backend
      (e.g., ``postgres``).
    * `version`: A positive integer identifying the version of the
      configuration data format used for the configuration data. This
      can be used by backends to mark backwards-incompatible format
      changes, so that older versions of RelRDF can simply reject to
      read the data.
    * `configData`: An arbitrary Python object
      used by the backend to represent the configuration
      internally.

    Both the `version` and `configData` parameters are normally
    obtained by invoking the
    :meth:`relrdf.config.ModelbaseConfig.freeze` on a configuration
    object.

    The return value must be an instance of
    :class:`relrdf.config.ModelbaseConfig`.
    An error of type :exc:`relrdf.error.ConfigurationError`
    will be raised if the data cannot be thawed.
    """

    # This is implemented this way in order to import only the modules
    # that are requested.

    try:
        module = _getModule(modelBaseType)
    except InstantiationError, e:
        raise ConfigurationError(str(e))

    configCls = module.ModelbaseConfig

    return configCls.thaw(version, configData)

def getModelBases():
    import db.mysql
    return {"postgres": db.postgres.modelbase.ModelBase}
