from error import InstantiationError


def getModelBase(modelBaseType, **modelBaseArgs):
    modelBaseTypeNorm = modelBaseType.lower()

    if modelBaseTypeNorm == "mysql":
        from db import mysql
        module = mysql
    elif modelBaseTypeNorm == "sqlite":
        from db import sqlite
        module = sqlite
    else:
        raise InstantiationError("invalid model base type '%s'"
                                 % modelBaseType)

    try:
        return module.getModelBase(**modelBaseArgs)
    except TypeError, e:
        raise InstantiationError(
            _("Missing or invalid model base arguments: %s") % e)

