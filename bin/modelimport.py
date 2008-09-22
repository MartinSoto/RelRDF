#!/usr/bin/env python

import sys

import relrdf
from relrdf.localization import _
from relrdf.error import InstantiationError
from relrdf.factory import parseCmdLineArgs


def error(msg):
    print >> sys.stderr, _("error: %s") % msg
    sys.exit(1)


if len(sys.argv) < 3:
    print >> sys.stderr, \
          _("usage: modelimport.py <file type> <file name> "
            ":<model base type> [<model base params] :<model type> "
            "[<model params>]")
    sys.exit(1)

fileType, fileName = sys.argv[1:3]

argv = list(sys.argv[3:])

try:
    baseType, baseArgs = parseCmdLineArgs(argv, 'model base')
    modelBase = relrdf.getModelBase(baseType, **baseArgs)

    sinkType, sinkArgs = parseCmdLineArgs(argv, 'sink')
    sink = modelBase.getSink(sinkType, **sinkArgs)
except InstantiationError, e:
    error(e)

fileType = fileType.lower() 
if fileType == 'rdfxml':
    from relrdf.modelimport import rdfxmlparse

    parser = rdfxmlparse.RdfXmlParser()
    parser.parse(fileName, sink)
elif fileType in ('v-modell', 'vmodell'):
    from relrdf.modelimport import vmodellparse

    vmodellparse.VModellParser(open(fileName), sink=sink)
elif fileType == 'xmi':
    from relrdf.modelimport import xmiparse

    parser = xmiparse.XmiParser()
    parser.parse(fileName, sink)
elif fileType == 'turtle':
    from relrdf.modelimport import librdfparse

    parser = redlandparse.RedlandParser(format='turtle')
    parser.parse(fileName, sink)
else:
    error(_("Invalid file type '%s'") % fileType)

sink.close()
modelBase.close()
