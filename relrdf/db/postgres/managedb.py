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

import getopt
import sys
from subprocess import call
from os import path

RDF_TERM_SQL = 'rdf_term/rdf_term.sql'
INITDB_SQL = 'initdb.sql'
SCHEMA_SQL = 'schema/create-basicschema-1.sql'
USER_SQL = 'schema/create-user.sql'

scriptDir = path.dirname(__file__)


def usage():    
    print """
Usage:
  python %s [OPTIONS] [ACTION]
  
Options:
  --help           This helpful text
  
  -d [name]        Database name (default: "relrdf")
  
  -h [name]        Server hostname 
  -p [port]        Server port
  -U [name]        Server login
  
Actions:
  --fast           Creates and initializes database "relrdf" and user "relrdf"

  --create-db      Creates the database
  --init-db        Initializes the database (clears existing data)
  
  --create-user=name  Create a new user
  --init-user=name    Give all necessary privileges to the specified user
""" % path.basename(sys.argv[0])
    exit(1)

def main():
    # Parse command line options
    argv = sys.argv[1:]
    try:
        shortOpts = "d:h:p:U:"
        longOpts = ["help", "fast", "create-db", "init-db", "create-user=",
                    "init-user="]
        opts, args = getopt.getopt(argv, shortOpts, longOpts)
    except getopt.GetoptError:
        usage()
    if args != []:
        usage()

    # Evaluate
    db = 'relrdf'
    createDB = False
    initDB = False
    createUsers = []
    initUsers = []
    pgOpts = []
    for opt, val in opts:
        if opt == '-d':
            db = val
        elif opt == '-h' or opt == '-p' or opt == '-U': 
            pgOpts.append(opt)
            pgOpts.append(val)
        elif opt == '--fast':
            createDB = initDB = True
            createUsers.append("relrdf")
            initUsers.append("relrdf")
        elif opt == '--help':
            usage()
        elif opt == '--create-db':
            createDB = True
        elif opt == '--init-db':
            initDB = True
        elif opt == '--create-user':
            createUsers.append(val)
        elif opt == '--init-user':
            initUsers.append(val)

    # Nothing to do?
    if not createDB and not initDB and createUsers == [] and initUsers == []:
        usage()
        sys.exit(1)

    # Create database.
    if createDB:
        call(['dropdb'] + pgOpts + [db])

        if 0 != call(['createdb'] + pgOpts + [db, "RelRDF database"]):
            print "Failed to create database '%s'!" % db
            exit(1)

        # rdf_term database extension.
        sqlFile = path.join(scriptDir, RDF_TERM_SQL)
        if 0 != call(['psql', '-d', db] + pgOpts + ['-f', sqlFile]):
            print "Failed to import rel_rdf extension into database '%s'!" % db
            print "Make sure rdf_term.so is installed!"
            exit(1)

        # General database initialization.
        sqlFile = path.join(scriptDir, INITDB_SQL)
        if 0 != call(['psql', '-d', db] + pgOpts + ['-f', sqlFile]):
            print "Failed to initialize database '%s'!" % db
            exit(1)

    # Initialize database.
    if initDB:    
        # The schema.
        sqlFile = path.join(scriptDir, SCHEMA_SQL)
        if 0 != call(['psql', '-d', db] + pgOpts + ['-f', sqlFile]):
            print "Failed to create schema for database '%s'!" % db
            exit(1)

    # Create user(s).
    for user in createUsers:     
        sqlFile = path.join(scriptDir, USER_SQL)
        if 0 != call(['createuser'] + pgOpts + ['-SDRlPE', user]):
            print "Failed to create user '%s' on database '%s'!" % (user, db)
            exit(1)

    # Initialize user(s).
    for user in initUsers:     
        sqlFile = path.join(scriptDir, USER_SQL)
        if 0 != call(['psql', '-d', db] + pgOpts +
                     ['-f', sqlFile, '-v', 'user=' + user]):
            print "Failed to initialize user '%s' in database '%s'!" \
                % (user, db)
            exit(1)

    print "\nAll done!"


if __name__ == '__main__':
    main()
