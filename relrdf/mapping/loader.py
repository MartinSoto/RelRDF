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
