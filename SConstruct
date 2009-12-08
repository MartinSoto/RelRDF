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


import os


env = Environment()

env.Append(CFLAGS='-g -O2')

# Environment for building Postgres-specific modules.
postgresEnv = env.Clone()

postgresEnv.Append(CPPPATH=[os.popen('pg_config --includedir-server')
                            .read()[:-1]])
postgresEnv.Replace(PKGLIBDIR=[os.popen('pg_config --pkglibdir')
                               .read()[:-1]])

postgresConf = Configure(postgresEnv)

if not postgresConf.CheckCHeader('postgres.h'):
        print 'Unable to find Postgres extension header file postgres.h'
        Exit(1)

postgresEnv = postgresConf.Finish()


Export('env', 'postgresEnv')

SConscript(['relrdf/sparql/SConscript',
            'relrdf/db/postgres/rdf_term/SConscript'])
