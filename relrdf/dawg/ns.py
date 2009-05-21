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


from relrdf.expression import uri

# Namespaces commonly used in DAWG test cases

rdf = uri.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
rdfs = uri.Namespace('http://www.w3.org/2000/01/rdf-schema#')

mf = uri.Namespace('http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#')
qt = uri.Namespace('http://www.w3.org/2001/sw/DataAccess/tests/test-query#')
dawgt = uri.Namespace('http://www.w3.org/2001/sw/DataAccess/tests/test-dawg#')
rs = uri.Namespace('http://www.w3.org/2001/sw/DataAccess/tests/result-set#')
