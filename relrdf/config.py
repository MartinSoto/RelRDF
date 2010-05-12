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

:mod:`config`: A Registry for Modelbase and Model Configuration Data
====================================================================

Depending on where and how a modelbase is physically stored, a
number of parameters may be required to access it. For
example, in order to access a modelbase stored in a Postgres database
server, the host name, database name, schema name, connection port,
user name, and password have to be correctly specified.

This module implements a registry for modelbase configuration data,
that makes it possible for users to store access and configuration
parameters localy for an arbitrary number of modelbases, and later
refer to them using a single name. This service makes it easier to
provide reasonable user interfaces for the RelRDF system.

Function :func:`getDefaultRegistry` in this module provides access to
a default instance of the modelbase registry. This single instance
should be enough to fulfill the needs of the large majority of users
of this module.

"""

import platform
import os
import tempfile
import json

from relrdf.localization import _
from relrdf.error import ConfigurationError
from relrdf import modelbasefactory


class ModelbaseConfig(object):
    """
    Interface for a modelbase configuration.

    Modelbase configurations are objects that uniquely identify a
    modelbase. The :meth:`getModelbase` method can be used to
    instantiate the actual modelbase from a configuration. The
    :meth:`thaw` and :meth:`freeze` methods can be used to "freeze" a
    configuration into a JSON-serializable form that can be stored
    persistently (see class :class:`ModelbaseRegistry`) and to later
    "thaw" this persistent representation back into a configuration
    object.
    """

    @staticmethod
    def thaw(version, configData):
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
        raise NotImplementedError

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
        raise NotImplementedError

    def getModelbase(self):
        """Return a live modelbase object corresponding to this
        configuration.
	"""
        raise NotImplementedError


class ModelbaseRegistry(object):
    """
    A file-based registry for modelbase configuration data.

    The registry is structured as a set of entries, each associated
    with a single modelbase and identified by a unique name. Each
    entry contains a backend identifier and version, a description,
    and an arbitrary object containing modelbase configuration
    data. The specific structure of these data is defined by each
    RelRDF backend.

    Also, for convenience, the registry keeps track of a default
    entry, that can be chosen freely among the stored entries. Many
    user-level operations can default to this entry when no modelbase
    is explicitly specified.

    Exceptions of type :exc:`ConfigurationError` will be raised by the
    methods in this class if the underlying storage file cannot be
    accessed apropriately. The massages in this exceptions are
    translatable and intented to be presented directly to the end
    user. Take into account that any of the class methods could
    potentially access the storage file.
    """

    __slots__ = ('fileName',
                 'entries',
                 'default',)

    DEFAULT_REGISTRY_NAME = os.path.join('relrdf', 'registry.json')
    """Default path to the registry file, relative to the user's home
    directory."""

    FORMAT_NAME = 'RelRDF modelbase registry'
    """Value of the root object's ``name`` field for all registry files."""

    FORMAT_VERSION = 1
    """Current registry format version."""

    def __init__(self, fileName=None):
        """
	The registry is stored in the file pointed to by `fileName`,
	which must be a string containing a file path. If left
        unspecified, a default value for `fileName` will be selected
        in a platform-specific fashion. For UNIX, the `XDG Base
        Directory Specification
        <http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html>`_
        is used to select this file location.

	The registry file and, if necessary, its containing
	directories will be created automatically if they do not exist
	when modifications to the registry are made.
	"""
        # Make sure that we have a location for our registry file.
        if fileName is None:
            fileName = os.environ.get('RELRDF_CONFIG')
            if fileName is None:
                system = platform.system()
                if system == 'Linux' or system == 'Unix':
                    fileName = self._getUnixPath()
                else:
                    raise ConfigurationError(
                        _("Cannot determine the location of the RelRDF "
                          "registry file. You can set the "
                          "RELRDF_CONFIG environment variable to an "
                          "appropriate file path (or contribute a patch "
                          "to support your operating system platform)"))

        self.fileName = os.path.abspath(fileName)
        """File name used by the registry."""

        self.entries = None
        """The registry entries. This is a dictionary associating entry
        names to contents. If `None`, entries have not been yet loaded
        from file."""

        self.default = None
        """The name of the default entry. If `None`, no default entry
        is set."""

        # Load the entries from the file. This leaves the dictionary
        # empty if the file does not yet exist.
        self._loadEntries()

    def _getUnixPath(self):
        """Return the default path for the RelRDF registry file under UNIX.
	"""
        configDir = os.environ.get('XDG_DATA_HOME')
        if configDir is None:
            home = os.environ.get('HOME')
            if home is None:
                raise ConfigurationError(
                        _("Cannot determine the location of the RelRDF "
                          "registry file. You must set at least one "
                          "of the XDG_DATA_HOME or HOME environment "
                          "variables in order for this to work"))
            return os.path.join(home, '.config', self.DEFAULT_REGISTRY_NAME)
        else:
            return os.path.join(configDir, self.DEFAULT_REGISTRY_NAME)

    def _loadEntries(self):
        """Load the entries from the registry file if they haven't
        been loaded already.
	"""
        if self.entries is not None:
            # Entries are already there.
            return

        if not os.path.exists(self.fileName):
            entries = {}
            default = None
        else:
            # Open the file and parse its contents.
            try:
                with open(self.fileName) as configFile:
                    try:
                        root = json.load(configFile)
                    except Exception, e:
                        raise ConfigurationError(
                            _("Unable to parse contents of RelRDF registry "
                              "file '%s' (%s)") % (self.fileName, unicode(e)))
            except OSError, e:
                raise ConfigurationError(
                    _("Cannot open RelRDF registry file "
                      "'%s' (%s). Make sure that you have the necessary "
                      "permisions") % (self.fileName, unicode(e)))

            # Check the root object.
            version = root.get('version')
            entries = root.get('entries')
            default = root.get('default')
            if not isinstance(root, dict) or \
                    root.get('name') != self.FORMAT_NAME or \
                    not isinstance(version, int) or \
                    version < 1 or \
                    not isinstance(entries, dict):
                raise ConfigurationError(
                    _("Unable to parse contents of RelRDF registry "
                      "file '%s'") % self.fileName)

            # Check the version.
            if version > self.FORMAT_VERSION:
                raise ConfigurationError(
                    _("This version of RelRDF is too old to handle "
                      "registry file '%s' (File format version is %d, "
                      "but only version %d is supported). You have to "
                      "upgrade your version of RelRDF, or point it to "
                      "another configuration directory") %
                    (self.fileName, version, self.FORMAT_VERSION))

            # Check the entries.
            #for name, value in entries.iteritems():

        # Set the object fields.
        self.entries = entries
        self.default = default

    def _saveEntries(self):
        """Write the entries to the registry file.
	"""
        if not os.path.exists(self.fileName):
            dirName = os.path.dirname(self.fileName)
            if not os.path.exists(dirName):
                # Create the directory.
                try:
                    os.makedirs(dirName)
                except OSError, e:
                    raise ConfigurationError(
                        _("Cannot create RelRDF's configuration directory "
                          "'%s' (%s). Make sure that you have the necessary "
                          "permisions") % (dirName, unicode(e)))
        else:
            # Rename the current registry file so that it becomes
            # a backup file.
            # TODO: Consider using a platform-specific backup name.
            backupName = self.fileName + '~'
            try:
                if os.path.exists(backupName):
                    os.remove(backupName)
                os.rename(self.fileName, backupName)
            except OSError, e:
                raise ConfigurationError(
                    _("Cannot create registry backup file '%s'. Make "
                      "sure that you have the necessary permisions") %
                    (backupName, unicode(e)))

        # Prepare the root object.
        root = {
            'name': self.FORMAT_NAME,
            'version': 1,
            'entries': self.entries,
            'default': self.default,
            }

        # Write the data. Since this file may contain passwords, we
        # make it unreadable to anyone but the user.
        try:
            origMask = os.umask(int('077', 8))
            with open(self.fileName, 'wb') as configFile:
                json.dump(root, configFile)
            os.umask(origMask)
        except OSError, e:
            raise ConfigurationError(
                _("Cannot write to registry file '%s' (%s). Make sure "
                  "that you have the necessary permisions and available "
                  "disk space. A backup copy of the registry file can "
                  "be found under '%s'") %
                (self.fileName, unicode(e)))

    def setRawEntry(self, name, backend, version, descr, configData):
        """Create or change a registry entry from raw configuration
        data.

	The parameters specify the entry contents:

	* `name`: The entry name; an arbitrary string. If an entry
          with the given name does not already exist in the registry,
          a new one will be created. Otherwise, the contents of the
          previously exiting entry will be replaced. This means that
          names are guaranteed to be unique in the registry.
	* `backend`: An arbitrary string identifying the RelRDF backend 
	  this antry applies to, e.g., ``"postgres"``.
	* `version`: A positive integer identifying the version of
          configuration data format used by the backend. This can be
          used by backends to mark backwards-incompatible format
          changes, so that older versions can simply reject to read
          the data.
	* `descr`: Descriptive text for the entry, usually provided by
	  the user creating the entry.
	* `configData`: Configuration data for the entry. This is an
	  arbitrary Python object that must be serializable using the
	  standard :mod:`json` module. The actual contents of this
	  object are backend-dependent and will normally be obtained
	  by parsing e.g., a command-line specification using a
	  backend-specific function. This class will only store and
	  retrieve the configuration data object without trying to
	  interpret it in any way.
	"""
        assert isinstance(name, basestring)
        assert isinstance(backend, basestring)
        assert isinstance(version, int) and version > 0
        assert isinstance(descr, basestring)

        self._loadEntries()
        self.entries[name] = {
            'backend': backend,
            'version': version,
            'descr': descr,
            'configData': configData,
            }
        self._saveEntries()

    def setEntry(self, name, descr, config):
        """Create or change a registry entry.

	The parameters specify the entry contents:

	* `name`: The entry name; an arbitrary string. If an entry
          with the given name does not already exist in the registry,
          a new one will be created. Otherwise, the contents of the
          previously exiting entry will be replaced. This means that
          names are guaranteed to be unique in the registry.
	* `descr`: Descriptive text for the entry, usually provided by
	  the user creating the entry.
	* `config`: A configuration object encapsulating the modelbase
	  configuration. It is expected to be an instance of
	  :class:`ModelbaseConfig`.
	"""
        backend, version, configData = config.freeze()
        self.setRawEntry(name, backend, version, descr, configData)

    def setDefaultEntry(self, default):
        """
	Make the entry named `default` the default entry.

	If the specified entry does not already exist in the registry,
	a :exc:`ConfigurationError` will be raised.
	"""
        self._loadEntries()
        if default not in self.entries:
            raise ConfigurationError(
                _("Cannot find modelbase '%s'") % default)
        self.default = default
        self._saveEntries()

    def getEntryNames(self):
        """
	Return a sequence (iterable) with all entry names in the
	registry in no particular order.

	The behavior of the returned iterator is undefined if the
	registry is changed while iteration is still in progress.
	"""
        return self.entries.iterkeys()

    def getDefaultName(self):
        """
	Return the name of the current default entry, or `None` if
        no default name is currently set.
	"""
        return self.default

    def getRawEntry(self, name=None):
        """Retrieve the raw contents of an entry.

	`name` identifies the entry to be retrieved. If it is `None`
	(the default), the registry's default entry (see
	:meth:`setDefaultEntry`) will be retrieved.

	The return value is a tuple of the form ``(backend, version,
	descr, configData)``.  This tuple's components correspond to
	the values of the similarly-named parameters given to the
	:meth:`setRawEntry` method while creating the entry.

	Raises a :exc:`ConfigurationError` if the specified entry does
	not exist in the registry.
	"""
        if name is None:
            name = self.default

        try:
            entry = self.entries[name]
        except KeyError:
            raise ConfigurationError(
                _("Cannot find modelbase '%s'") % name)
 
        return (entry['backend'], entry['version'], entry['descr'],
                entry['configData'],)

    def getEntry(self, name=None):
        """Retrieve the contents of an entry.

	`name` identifies the entry to be retrieved. If it is `None`
	(the default), the registry's default entry (see
	:meth:`setDefaultEntry`) will be retrieved.

	The return value is a tuple of the form ``(descr,
	config)``.  This tuples's components correspond to 
	the values of the similarly-named parameters given to the
	:meth:`setEntry` method while creating the entry.

	Raises a :exc:`ConfigurationError` if the specified entry does
	not exist in the registry.
	"""
        backend, version, descr, configData = self.getRawEntry(name)
        config = modelbasefactory.thawModelbaseConfig(backend, version,
                                                      configData)
        return (descr, config)

    def removeEntry(self, name):
        """
	Remove the entry identified by `name` from the registry.

	Raises a :exc:`ConfigurationError` if the specified entry does
	not exist in the registry.
	"""
        self._loadEntries()
        try:
            del self.entries[name]
        except KeyError:
            raise ConfigurationError(
                _("Cannot find modelbase '%s'") % name)

        if name == self.default:
            self.default = None

        self._saveEntries()

    def getFileName(self):
        """
	Return the path to the file where this registry is stored.
	"""
        return self.fileName


_defaultRegistry = None
"""The default registry instance."""

def getDefaultRegistry():
    """Returns the default modelbase registry."""
    global _defaultRegistry

    if _defaultRegistry is None:
        _defaultRegistry = ModelbaseRegistry()

    return _defaultRegistry
