#!/usr/bin/env python
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (C) 2005-2009, Fraunhofer Institut Experimentelles
# Software Engineering (IESE).
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

import sys

import relrdf
from relrdf.localization import _
from relrdf.error import InstantiationError
from relrdf.factory import parseCmdLineArgs

from urlparse import urljoin

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
    if 'baseGraph' not in sinkArgs:
        sinkArgs['baseGraph'] = urljoin('file:', fileName)
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
    from relrdf.modelimport import redlandparse

    parser = redlandparse.RedlandParser(format='turtle')
    parser.parse(fileName, sink)
else:
    error(_("Invalid file type '%s'") % fileType)

sink.close()
modelBase.close()