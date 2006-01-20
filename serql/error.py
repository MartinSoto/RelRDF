import antlr


class Error(Exception):
    """Base class for exceptions raised when parsing SerQL queries."""

    def __init__(self, msg):
        Exception.__init__(self, msg)

        self.msg = msg


class PositionError(Error):
    """Base class for SerQL exceptions containing an error position."""

    def __init__(self, line=None, column=None, fileName=None, **kwargs):
        Error.__init__(self, **kwargs)

        self.line = line
        self.column = column
        self.fileName = fileName

    def __str__(self):
        if self.column:
            return "%s:%d:%d: %s" % (self.fileName, self.line,
                                     self.column, self.msg)
        else:
            return "%s:%d: %s" % (self.fileName, self.line, self.msg)


class SyntaxError(PositionError):
    """A SerQL syntax error."""

    @staticmethod
    def create(orig):
        if isinstance(orig, antlr.RecognitionException):
            if isinstance(orig, antlr.NoViableAltException):
                # antlr.NoViableAltException is broken and doesn't set the
                # position properly.
                line = orig.token.getLine()
                column = orig.token.getColumn()
                fileName = None
            else:
                if orig.line != -1:
                    line = orig.line
                else:
                    line = None
                if orig.column != -1:
                    column = orig.column
                else:
                    column = None
                fileName = orig.fileName

            if isinstance(orig, antlr.MismatchedCharException) or \
                   isinstance(orig, antlr.NoViableAltForCharException):
                msg = _("unexpected character '%s'") % orig.foundChar
            elif isinstance(orig, antlr.MismatchedTokenException) or \
                     isinstance(orig, antlr.NoViableAltException):
                msg = _("unexpected token '%s'") % orig.token.getText()
            else:
                return None

            new = SyntaxError(msg=msg, line=line, column=column,
                              fileName=fileName)
        else:
            return None

        new.originalException = orig

        return new


class SemanticError(PositionError):
    """A SerQL semantic error."""
    pass
