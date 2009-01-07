#!/bin/sh

# Wrong parameter count?
if ! [ -n "$2" ] || [ -n "$3" ]
then
  echo Usage:
  echo "  ./create-basicschema.sh [database] [user]"
  exit
fi

# Create user
createuser -SDRlPE $2

# Grant
psql -d $1 -f create-user.sql -v user=$2

