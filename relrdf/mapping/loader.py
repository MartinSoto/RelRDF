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


import os
from os import path

import parseenv


schemaPath = []
"""A list of directory names used to look for schemas."""

rawPath = os.environ.get('RELRDF_SCHEMA_PATH', '.')
schemaPath = rawPath.split(':')
    

def loadSchema(name):
    """Search for a schema file and load it."""
    global schemaPath

    stream = None
    for dirName in schemaPath:
        try:
            stream = file(path.join(dirName, '%s.schema' % name))
            break
        except IOError:
            pass

    if stream is None:
        return None

    env = parseenv.ParseEnvironment()
    return env.parseSchema(stream)


if __name__ == '__main__':
    import sys

    schema = loadSchema(sys.argv[1])
