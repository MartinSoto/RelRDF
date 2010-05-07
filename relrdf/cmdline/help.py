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

"""
Support operations for help text printing
"""

import itertools
import os
import textwrap


def ioctl_TIOCGWINSZ(fd):
    try:
        import fcntl, termios, struct
        cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
                                             '1234'))
    except:
        return None
    return cr

def getTerminalSize():
    """Make a reasonable attempt at determining the current terminal
    size.

    Returns a pair of integers ``(lines, columns)``.
    """
    # Try the TIOCGWINSZ ioctl on the standard input and output streams.
    cr = ioctl_TIOCGWINSZ(0) or ioctl_TIOCGWINSZ(1) or ioctl_TIOCGWINSZ(2)

    if not cr:
        # Otherwise, try TIOCGWINSZ on the terminal file (/dev/tty or
        # similar).
        try:
            import os
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_TIOCGWINSZ(fd)
            os.close(fd)
        except:
            pass

    if not cr:
        # As a last resort, try the LINES and COLUMNS environment
        # variables.
        try:
            cr = (int(os.environ['LINES']), int(os.environ['COLUMNS']))
        except:
            # If everything else fails, use sensible values.
            cr = (24, 80)

    return cr
 
def wrapText(text, width=None, indent=0, firstIndent=None):
    """Rewrap a string of text possibly containing several paragraphs.

    The text will be rewrapped to a fixed width, and optionally
    indented. `text` is the text to rewrap, with paragraphs separated
    by one or more blank lines. `width` is the total text width,
    including indentation (defaults to the current terminal width
    minus 2). `indent` is the width of the indentation (defaults to
    0).

    If `firstIndent` is not ``None`` (the default) it will be used as
    indent text for the first line, instead of the usual whitespace
    characters. If its length is less than `indent`, it will be padded
    with white space to the right until that length is reached.

    The return value is an iterator over the sequence of wrapped
    lines. The returned lines do not include their final newline
    characters.
    """
    indentSp = ' ' * indent

    if width is None:
        lines, columns = getTerminalSize()
        width = columns - indent - 2

    if firstIndent is None:
        indentTxt = indentSp
    else:
        if len(firstIndent) < indent:
            indentTxt = firstIndent + ' ' * (indent - len(firstIndent))
        else:
            indentTxt = firstIndent

    firstPar = True
    lines = (line.strip() for line in text.split('\n'))
    for isPar, parLines in itertools.groupby(lines,
                                             lambda line: len(line) != 0):
        if not isPar:
            continue

        if firstPar:
            firstPar = False
        else:
            yield ''

        for parLine in textwrap.wrap(' '.join(parLines), width):
            yield indentTxt + parLine
            indentTxt = indentSp
