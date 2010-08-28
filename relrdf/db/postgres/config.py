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


"""Configuration support for the Postgres backend.
"""

from relrdf.localization import _

from relrdf.error import InstantiationError
from relrdf.config import Configuration
from relrdf.cmdline import ArgumentParser


class PostgresConfiguration(Configuration):
    __slots__ = ()

    name = 'postgres'
    version = 1
    schema = {
        'host': {
            'type': str,
            'default': None,
            },
        'database': {
            'type': str,
            },
        'schema': {
            'type': str,
            'default': None,
            },
        'user': {
            'type': str,
            'default': None,
            },
        'password': {
            'type': str,
            'default': None,
            },
        }

    @classmethod
    def _createCmdLineParser(cls):
        parser = ArgumentParser(
            description=_("Options to access modelbases stored as "
                          "Postgres databases"))

        parser.add_argument('--database', '--db', metavar='DB',
                            help=_("connect to database DB (required)"),
                            required=True)
        parser.add_argument('--host', metavar='HOST',
                            help=_("connect to host HOST (defaults to "
                                   "local host)"))
        parser.add_argument('--user', metavar='USER',
                            help=_("connect as user USER (defaults to "
                                   "current user name)"))
        parser.add_argument('--password', '--pw', metavar='PW',
                            help=_("authenticate using password PW"))

        return parser


class PlainModelConfiguration(Configuration):
    __slots__ = ()

    name = 'plain'
    version = 1
    schema = {
        'graphid': {
            'type': str,
            },
        }

    @classmethod
    def _createCmdLineParser(cls):
        parser = ArgumentParser(
            description=_("Options to access plain graphs"))

        parser.add_argument('--graphid', '--uri', metavar='URI',
                            help=_("set the graph identified by URI "
                                   "as default graph"),
                            required=True)

        return parser


def getConfigClass(path):
    if len(path) == 0:
        return PostgresConfiguration
    elif path[0] == 'plain':
        return PlainModelConfiguration
    else:
        raise InstantiationError(_("'%s' is not a valid model type for a "
                                   "Postgres modelbase") % path[0])
