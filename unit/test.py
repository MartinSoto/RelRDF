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


import sys
import os

baseDir = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
sys.path.insert(0, baseDir)

import unittest

# Import test modules.
import argparse
import cmdline
import config

testModules = [argparse, cmdline, config]


if len(sys.argv) == 1:
    moduleSuites = [unittest.defaultTestLoader.loadTestsFromModule(module)
                    for module in testModules]
else:
    moduleSuites = []
    for modName in sys.argv[1:]:
        modList = [module for module in testModules
                   if module.__name__ == modName]
        if len(modList) == 0:
            print >> sys.stderr, "Test module '%s' not found" % modName
            sys.exit(1)
    moduleSuites.append(unittest.defaultTestLoader. \
                            loadTestsFromModule(modList[0]))

mainSuite = unittest.TestSuite(moduleSuites)
unittest.TextTestRunner(verbosity=2).run(mainSuite)
