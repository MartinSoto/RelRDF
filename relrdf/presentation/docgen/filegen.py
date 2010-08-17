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

import os
import shutil

from core import ContextObject


class FileGenerator(ContextObject):
    __slots__ = ()

    def absPath(self, relPath):
        return os.path.normpath(os.path.join(self.context.destPath,
                                             relPath))

    def makeDirForFileAbs(self, absPath):
        dirName, baseName = os.path.split(absPath)
        if os.path.isfile(dirName):
            raise IOError, \
                "Cannot create directory '%s': file on the way" % dirName
        if os.path.isdir(dirName):
            return
        self.makeDirForFileAbs(dirName)
        os.mkdir(dirName)

    def makeDirForFile(self, relPath):
        self.makeDirForFileAbs(self.absPath(relPath))

    def openGenFile(self, relPath):
        self.makeDirForFile(relPath)
        return file(self.absPath(relPath), 'w')

    def copyStaticFile(self, srcRelPath, destRelPath):
        self.makeDirForFile(destRelPath)
        for dirPath in self.context.staticPath:
            srcPath = os.path.join(dirPath, srcRelPath)
            if os.path.isfile(srcPath):
                shutil.copyfile(srcPath, self.absPath(destRelPath))
                return
        raise IOError, \
            "Cannot find file '%s' in static path" % srcRelPath
