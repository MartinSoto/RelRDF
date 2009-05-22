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


from relrdf.localization import _
from error import InstantiationError


def getModelBase(modelBaseType, **modelBaseArgs):
    modelBaseTypeNorm = modelBaseType.lower()

    if modelBaseTypeNorm == "postgres":
        from db import postgres
        module = postgres
    elif modelBaseTypeNorm == "debug":
        import basesinks
        module = basesinks
    else:
        raise InstantiationError("invalid model base type '%s'"
                                 % modelBaseType)

    try:
        return module.getModelBase(**modelBaseArgs)
    except TypeError, e:
        raise InstantiationError(
            _("Missing or invalid model base arguments: %s") % e)

def getModelBases():
    import db.mysql
    return {"postgres": db.postgres.modelbase.ModelBase}
