from db import mysql


def getModelBase(modelBaseType, **modelBaseArgs):
    modelBaseTypeNorm = modelBaseType.lower()
    if modelBaseTypeNorm == "mysql":
        return mysql.getModelBase(**modelBaseArgs)
    else:
        assert False, "invalid model base type '%s'" % modelBaseType
