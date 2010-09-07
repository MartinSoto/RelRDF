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


# Put public API elements in this module:

# Error classes.
from error import *

# Result types.
from results import RESULTS_COLUMNS, RESULTS_STMTS, RESULTS_MODIF, \
    RESULTS_EXISTS, RESULTS_ASK

# The basic building blocks of RDF.
from relrdf.expression.uri import Uri, Namespace
from relrdf.expression.literal import Literal

# Common namespaces.
import commonns as ns

# URI shortener service.
from relrdf.util.nsshortener import NamespaceUriShortener

# Factory function to create model bases. Indirectly, this gives access
# to queryable model objects.
from centralfactory import getModelbase

# Factory function for creating query templates.
from parsequery import makeTemplate, parseQuery

# Graph API.
import graph
