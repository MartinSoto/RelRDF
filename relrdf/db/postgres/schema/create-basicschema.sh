#!/bin/sh

# Wrong parameter count?
if ! [ -n "$1" ] || [ -n "$2" ]
then
  echo Usage:
  echo "  ./create-basicschema.sh [database]"
  exit
fi

# Create database
if ! createdb $1 "RelRDF database"
then
	exit
fi

# Import rdf_term
psql -d $1 -f ../rdf_term/rdf_term.sql

# Import schema
psql -d $1 -f create-basicschema.sql

