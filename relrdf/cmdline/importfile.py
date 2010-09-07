# -*- coding: utf-8 -*-
# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (C) 2005-2009 Fraunhofer Institut Experimentelles
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

"""Implementation of the import command-line operation."""


import sys
from urlparse import urljoin

from relrdf.localization import _
from relrdf.error import CommandLineError, ConfigurationError, \
    InstantiationError
from relrdf import centralfactory
from relrdf import config

import backend


class ImportOperation(backend.CmdLineOperation):
    """Import an RDF model from a file into a RelRDF modelbase

    Imports the file named FILE, which is expected to be of type TYPE
    into the specified modelbase and model. Several file types are
    supported. You must use the --type option to select the
    appropriate one (file type autodetection is planned for a future
    version).
    """

    __slots__ = ()

    name = 'import'

    needsModelConf = True

    def makeParser(self):
        parser = super(ImportOperation, self).makeParser()

        parser.add_argument('--type', '-t',
                            metavar=_("TYPE"), dest='type', required=True,
                            help=_("Type of the input file to import"))
        parser.add_argument('file', metavar=_("FILE"),
                            help=_("Path to the file to import"))

        return parser

    def run(self, options, mbConf=None, modelConf=None, **kwArgs):
        fileType, fileName = options.type, options.file

        argv = list(sys.argv[3:])

        try:
            modelBase = centralfactory.getModelbase(mbConf)
            #if 'baseGraph' not in sinkArgs:
            #    sinkArgs['baseGraph'] = urljoin('file:', fileName)
            sink = modelBase.getSink(modelConf)
        except InstantiationError, e:
            raise CommandLineError(e)

        fileType = fileType.lower()
        if fileType == 'rdfxml':
            from relrdf.modelimport import rdfxmlparse

            parser = rdfxmlparse.RdfXmlParser()
            try:
                parser.parse(fileName, sink)
            except Exception, e:
                raise CommandLineError(e)
        elif fileType in ('v-modell', 'vmodell'):
            from relrdf.modelimport import vmodellparse

            try:
                vmodellparse.VModellParser(open(fileName), sink=sink)
            except Exception, e:
                raise CommandLineError(e)
        elif fileType == 'xmi':
            from relrdf.modelimport import xmiparse

            parser = xmiparse.XmiParser()
            try:
                parser.parse(fileName, sink)
            except Exception, e:
                raise CommandLineError(e)
        elif fileType == 'turtle':
            from relrdf.modelimport import redlandparse

            parser = redlandparse.RedlandParser(format='turtle')
            try:
                parser.parse(fileName, sink)
            except Exception, e:
                raise CommandLineError(e)
        elif fileType == 'ntriples':
            from relrdf.modelimport import redlandparse

            parser = redlandparse.RedlandParser(format='ntriples')
            try:
                parser.parse(fileName, sink)
            except Exception, e:
                raise CommandLineError(e)
        else:
            raise CommandLineError(_("Invalid file type '%s'") % fileType)

        modelBase.commit()

        sink.close()
        modelBase.close()
