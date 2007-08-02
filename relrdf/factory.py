"""Utility classes and procedures for creating factories."""

import re

from relrdf.localization import _
from relrdf.error import InstantiationError


def _parseError(msg, objectName):
    raise InstantiationError(_("While creating %s: %s") % (objectName, msg))

_argSpecPattern = re.compile(r'([A-Za-z_][A-Za-z_0-9]+) *= *(.*)')

def parseCmdLineArgs(argv, objectName):
    """Parses a set of command-line arguments for a factory."""

    if len(argv) == 0:
        _parseError(_("no type specified"), objectName)

    if argv[0][0] != ':':
        _parseError(_("type specification '%s' must start with colon")
                    % argv[0], objectName)
    typeName = argv[0][1:]

    parsedArgs = {}
    i = 1
    while i < len(argv) and argv[i][0] != ':':
        m = _argSpecPattern.match(argv[i])
        if m is None:
            _parseError(_("incorrect parameter specification '%s'") % argv[i],
                        objectName)
            break

        parsedArgs[m.group(1)] = m.group(2)

        i += 1

    # Remove all parsed elements from argv.
    argv[:i] = []

    return typeName, parsedArgs

