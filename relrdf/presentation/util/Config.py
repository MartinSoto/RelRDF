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
import ConfigParser

class CaseSensitiveConfigParser(ConfigParser.ConfigParser):
    def optionxform(self, option):
        return str(option)


def getCFGFilename(dirname):
    if os.name == "nt" or os.name == "ce":
        path = os.environ.get("APPDATA", os.curdir)
        prefix = ""
    elif os.name == "posix":
        path = os.environ.get("HOME", os.curdir)
        prefix = "."
    else:
        path = os.curdir
        prefix = ""
    try:
        os.makedirs(path + os.sep + prefix + dirname)
    except OSError:
        pass
    return path + os.sep + prefix + dirname + os.sep
