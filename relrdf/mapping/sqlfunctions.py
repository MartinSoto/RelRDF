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


from relrdf import error
from relrdf.expression import nodes, constnodes


class SqlFunction(object):
    """Representation of a SQL function."""

    __slots__ = ()

    hasEval = False
    """If true, this class implements the evaluate method."""

    @staticmethod
    def evaluate(name, *args):
        """Evaluates the function on the given arguments.

        The arguments and the result are standard python
        values. `name` is the name used to call the function."""
        raise NotImplementedError

    @classmethod
    def evalExpr(cls, name, *args):
        """Evaluates the function on the given arguments.

        The arguments and the result must be constant nodes (nodes.Uri
        or nodes.Literal). `name` is the name used to call the
        function.

        This method raises a `NotImplementedError` if the class has no
        suitable `evaluate` implementation or a `ValueError` if anyone
        of the arguments is not constant."""
        if not cls.hasEval:
            raise NotImplementedError
        return nodes.Literal(cls.evaluate(name,
                                          *constnodes.constValues(args,
                                                                  all=True)))


class Length(SqlFunction):
    """SQL length function."""

    hasEval = True

    @staticmethod
    def evaluate(name, string):
        return len(string)


class Substring(SqlFunction):
    """SQL substring function."""

    hasEval = True

    @staticmethod
    def evaluate(name, string, pos, length=None):
        if length is None:
            length = string.len()
        if pos >= 1:
            pos -= 1
        return string[pos:pos + length]


_functions = {
    'len': Length,
    'length': Length,
    'substr': Substring,
    'substring': Substring,
    }


class SqlFunctionError(error.Error):
    """Base class for errors hapenning while working with SQL
    functions."""
    pass


class StaticEvalError(error.Error):
    """Used to report the case where a function cannot be evaluated
    statically."""
    pass


def evalFunction(name, *args):
    """Evaluates a SQL function on the given arguments.

    The arguments and the result must be constant nodes (nodes.Uri
    or nodes.Literal).

    Raises a `StaticEvalError` if the function cannot be evaluated
    statically."""
    try:
        return _functions[name].evalExpr(name, *args)
    except NotImplementedError, e:
        raise StaticEvalError(str(e))
    except ValueError, e:
        raise StaticEvalError(str(e))
    except KeyError, e:
        raise StaticEvalError(str(e))

