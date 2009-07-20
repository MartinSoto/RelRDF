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


# Possible result types.
RESULTS_COLUMNS = 10
RESULTS_STMTS = 11
RESULTS_MODIF = 12


class ModifResults(object):
    """A results object used to report the result of a modification
    operation."""

    __slots__ = ('affectedRows')

    def __init__(self, affectedRows):
        self.affectedRows = affectedRows

    def resultType(self):
        return RESULTS_MODIF

    length = 0

    def iterAll(self):
        # This is a generator producing the empty sequence.
        if False:
            yield None

    __iter__ = iterAll
