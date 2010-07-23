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


"""
"""

from relrdf.localization import _
from relrdf.error import ConfigurationError


class Configuration(object):
    """
    Configuration base class.

    Configurations are objects that uniquely identify a modelbase, a
    model or other similar object. The :meth:`thaw` and :meth:`freeze`
    methods can be used to "freeze" a configuration into a
    JSON-serializable form that can be stored persistently (see class
    :class:`Registry`) and to later "thaw" this persistent
    representation back into a configuration object.
    """

    __slots__ = ('params',)

    name = None
    version = None
    schema = {}

    _cmdLineParser = None 

    def __init__(self, **kwArgs):
        self.params = {}

        # Set parameters from the argument list.
        for name, value in kwArgs.iteritems():
            try:
                paramSchema = self.schema[name]
            except KeyError:
                raise ConfigurationError, _("unexpected configuration "
                                            "parameter '%s'") % name
            if not isinstance(value, paramSchema['type']):
                raise ConfigurationError, _("invalid type for configuration "
                                            "parameter '%s'") % name
            self.params[name] = value

        # Set remaining parameters to their default values.
        for name, paramSchema in self.schema.iteritems():
            if name not in self.params:
                try:
                    default = paramSchema['default']
                except KeyError:
                    raise ConfigurationError, _("required parameter '%s' "
                                                "not specified") % name
                self.params[name] = default

    def getParam(self, name):
        return self.params[name]

    def getParams(self):
        return dict(self.params)

    def freeze(self):
        """Return a static, JSON-serializable ("frozen")
        representation of this object.

	The return value is a tuple of the form ``(backend, version,
        configData)``:

	* `backend`: a string identifying the backend.
	* `version` is a positive integer indicating the format
          version for the returned configuration data.
	* `configData` is an arbitrary Python object, which must be
          serializable using the standard :mod:`json` module.

	These values can be passed to the
        :func:`modelbasefactory.thawModelbaseConfig` to produce a
        configuration object that is equivalent to this one. This
        function, in turn, calls the :meth:`thaw` method in this
        class.
	"""
        return (self.name, self.version, self.params)

    @classmethod
    def thaw(cls, version, data):
        """Create a configuration object from serialized ("frozen") data.

        `version` is a positive integer indicating the format version
        for the returned configuration data. `configData` is an
        arbitrary, JSON-serializable Python object used by the backend
        to represent the configuration internally. Both values are
        normally originally obtained by running the :meth:`freeze` on
        an instance of this class.

	The return value must be an instance of this class. A
        :exc:`ConfigurationError` will be raised if the data cannot be
        thawed.
	"""
        if int(version) != int(cls.version):
            raise ConfigurationError("Version %d of config data is not "
                                     "supported. Upgrade RelRDF" % version)
        return cls.fromUnchecked(**data)

    @classmethod
    def fromUnchecked(cls, **kwArgs):
        # Convert parameters from the argument list to their expected
        # types.
        for name, value in kwArgs.iteritems():
            try:
                paramSchema = cls.schema[name]
            except KeyError:
                raise ConfigurationError, _("unexpected configuration "
                                            "parameter '%s'") % name
            kwArgs[name] = paramSchema['type'](value)

        # Create the actual object.
        return cls(**kwArgs)

    @classmethod
    def _createCmdLineParser(cls):
        raise NotImplementedError

    @classmethod
    def _getCmdLineParser(cls):
        if cls._cmdLineParser is None:
            cls._cmdLineParser = cls._createCmdLineParser()
        return cls._cmdLineParser

    @classmethod
    def fromCmdLine(cls, args):
        options = cls._getCmdLineParser().parse_args(args)

        kwArgs = {}
        for name, paramSchema in cls.schema.iteritems():
            try:
                kwArgs[name] = getattr(options, name)
            except AttributeError:
                kwArgs[name] = None

            if kwArgs[name] is None:
                try:
                    kwArgs[name] = paramSchema['default']
                except KeyError:
                    raise ConfigurationError, _("unexpected configuration "
                                                "parameter '%s'") % name

        return cls.fromUnchecked(**kwArgs)

    @classmethod
    def cmdLineHelp(cls):
        return cls._getCmdLineParser().format_help()

    def readableContents(self):
        pass
