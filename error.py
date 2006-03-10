import antlr

from expression import nodes


class Error(Exception):
    """Base class for exceptions raised when parsing queries."""

    def __init__(self, msg):
        Exception.__init__(self, msg)

        self.msg = msg


class PositionError(Error):
    """Base class for exceptions containing an error position."""

    def __init__(self, extents=None, **kwargs):
        Error.__init__(self, **kwargs)

        self.extents = extents

    def __str__(self):
        if self.extents is None:
            return self.msg
        else:
            if self.extents.fileName is not None:
                fileName = self.extents.fileName
            else:
                fileName = _("<unknown>")

            if self.extents.endColumn is None:
                endPos = ""
            elif self.extents.endColumn is None:
                endPos = " (ends: line %d)" % self.extents.endLine
            else:
                endPos = " (ends: line %d, col %d)" % \
                         (self.extents.endLine,
                          self.extents.endColumn)

            if self.extents.startLine is None:
                return "%s:%s %s" % (fileName, endPos, self.msg)
            elif self.extents.startColumn is None:
                return "%s:%d:%s %s" % (fileName, self.extents.startLine,
                                        endPos, self.msg)
            else:
                return "%s:%d:%d:%s %s" % (fileName,
                                         self.extents.startLine,
                                         self.extents.startColumn,
                                         endPos, self.msg)


class SyntaxError(PositionError):
    """A syntax error."""

    @staticmethod
    def create(orig):
        if isinstance(orig, antlr.RecognitionException):
            extents = nodes.NodeExtents()

            if isinstance(orig, antlr.NoViableAltException):
                # antlr.NoViableAltException is broken and doesn't set the
                # position properly.
                extents.setFromToken(orig.token)
            else:
                if orig.line != -1:
                    extents.startLine = orig.line
                else:
                    extents.startLine = None
                if orig.column != -1:
                    extents.startColumn = orig.column
                else:
                    extents.startColumn = None
                extents.fileName = orig.fileName

            if isinstance(orig, antlr.MismatchedCharException) or \
                   isinstance(orig, antlr.NoViableAltForCharException):
                msg = _("unexpected character '%s'") % orig.foundChar
            elif isinstance(orig, antlr.MismatchedTokenException) or \
                     isinstance(orig, antlr.NoViableAltException):
                extents.setFromToken(orig.token)
                msg = _("unexpected token '%s'") % orig.token.getText()
            else:
                return None

            new = SyntaxError(msg=msg, extents=extents)
        else:
            return None

        new.originalException = orig

        return new


class SemanticError(PositionError):
    """A semantic error."""
    pass


class TypeCheckError(PositionError):
    """A type checking error."""
    pass
