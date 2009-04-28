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


import antlr

from relrdf.localization import _
from relrdf.expression import nodes


class Error(Exception):
    """Base class for RelRDF errors."""

    def __init__(self, msg):
        Exception.__init__(self, msg)

        self.msg = msg


class InstantiationError(Error):
    """Exception class for errors happening when instantiating objects
    from factories."""
    pass


class AuthenticationError(Error):
    """Exception class for errors related to user authentication."""
    pass


class DatabaseError(Error):
    """Exception class for database related errors."""
    pass


class MacroError(Error):
    """Exception class for errors related to macro expressions
    processing."""
    pass


class ModifyError(Error):
    """Exceptiom class for errors related to modifying models.
    """
    pass


class TemplateError(Error):
    """Exception class for errors related to query templates.
    """
    pass


class SerializationError(Error):
    """Exception class for errors related to model serialization.
    """
    pass


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

            if self.extents.endLine is None:
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


class SchemaError(PositionError):
    """An error produced while working with macro-based schemas."""
    pass


class NotSupportedError(PositionError):
    """Exception raised when there is an attempt to use planned, but
    not yet supported features from a query language."""
    pass
