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


def raises(exc):
    """Decorator for test methods that are expected to raise
    exceptions.

    `exc` is the expected exception class or a tuple containing
    several possible expected exception classes, and is passed to the
    :meth:`unittest.TestCase.assertRaises` method.
    """

    def decorate(method):
        def wrap(self, *args, **keywords):
            self.assertRaises(exc, method, self, *args, **keywords)

        return wrap

    return decorate
