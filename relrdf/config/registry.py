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

Depending on where and how modelbase and models are physically stored,
a number of parameters may be required to access them. For example, in
order to access a modelbase stored in a Postgres database server, the
host name, database name, schema name, connection port, user name, and
password have to be correctly specified.

This module implements a registry for modelbase and model
configuration data, that makes it possible for users to store access
and configuration parameters localy for an arbitrary number of
modelbases and models, and later refer to them by specifying a single
name, or more exactly, a single path in the registry. This service
makes it easier to provide reasonable user interfaces for the RelRDF
system.

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


class Registry(object):
    """
    A file-based registry for configuration data.

    The registry is structured as an n-ary tree of entries, each
    associated with a single modelbase or model (although other
    objects could be covered as well). The subentries of a particular
    nodes are identified by unique names (arbitrary unicode
    strings). This way, entries in the tree are uniquely identified by
    the path of names leading to them from the root node.

    Each entry contains a backend identifier and version, a
    description, and an arbitrary object with modelbase configuration
    data. The specific structure of these data is defined by each
    RelRDF backend. Every entry can have an arbitrary number of
    similarly structured subentries (n-ary tree structure).

    Also, for convenience, the registry keeps track of a default entry
    in each node that can be chosen freely among the stored
    entries. Many user-level operations default to this entry when
    none is explicitly specified.

    Exceptions of type :exc:`ConfigurationError` will be raised when
    any of the methods of this class cannot complete its task. In
    particular, they will be raised if the underlying storage file
    cannot be accessed apropriately. Take into account that any of the
    class methods could potentially access the storage file. The
    messages in these exceptions are translatable and appropriate for
    being presented directly to end users.

    Several operations in this class have parameters named
    ``path``. Those are always expected to be tuples ((or compatible
    objects such as lists) of strings. The entry identified by a path
    is retrieved by going to the tree's root entry, and retrieving
    subentries down the tree according to names in the path. This way,
    the empty path ``()`` identifies the root entry, and the path
    ``('a', 'b')`` identifies entry the entry named "b" which is a
    subentry of entry "a", which, in turn, is a subentry of the root
    entry.

    When a path component is ``None``, the default subentry in the
    corresponding node will be used instead. Notice that, at any given
    time, a particular entry may not have a default subentry. An error
    will result if a path tries to use the default subentry for such
    an entry.
    """

    __slots__ = ('fileName',
                 'rootNode',)

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

        self.rootNode = None
        # TODO: Documentation
        """"""

        # Load the node structure from the file. This creates an empty
        # root node if the file does not yet exist.
        self._loadData()

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

    def _loadData(self):
        """Load the tree from the registry file if it was not loaded already.
	"""
        if self.rootNode is not None:
            # A root node is already there.
            return

        if not os.path.exists(self.fileName):
            # Create an empty root object.
            self.rootNode = {
                'name': self.FORMAT_NAME,
                'version': 1,
                'entries': {},
                'default': None,
                }
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
            if not isinstance(root, dict) or \
                    root.get('name') != self.FORMAT_NAME or \
                    not isinstance(version, int) or \
                    version < 1 or \
                    not isinstance(root.get('entries'), dict):
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

            # Store the persistent object.
            self.rootNode = root

    def _saveData(self):
        """Write the tree to the registry file.
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

        # Write the data. Since this file may contain passwords, we
        # make it unreadable to anyone but the user.
        try:
            origMask = os.umask(int('077', 8))
            with open(self.fileName, 'wb') as configFile:
                json.dump(self.rootNode, configFile)
            os.umask(origMask)
        except OSError, e:
            raise ConfigurationError(
                _("Cannot write to registry file '%s' (%s). Make sure "
                  "that you have the necessary permisions and available "
                  "disk space. A backup copy of the registry file can "
                  "be found under '%s'") %
                (self.fileName, unicode(e)))

    def _getNode(self, path):
        """Return the node corresponding to `path`."""
        node = self.rootNode
        for i, name in enumerate(path):
            if name is None:
                name = node.get('default')
                if name is None:
                    if i == 0:
                        raise ConfigurationError(
                            _("No default set for toplevel configuration"))
                    else:
                        raise ConfigurationError(
                            _("Configuration entry '%s' has no default set") %
                            ':'.join(path[:i - 1]))

            entries = node.get('entries')
            node = entries is not None and entries.get(name)
            if node is None:
                if i == 0:
                    raise ConfigurationError(
                        _("No toplevel configuration '%s'") % name)
                else:
                    raise ConfigurationError(
                        _("Configuration entry '%s' has no subentry '%s'") %
                        (':'.join(path[:i - 1]), name))

        return node

    def setRawEntry(self, path, backend, version, descr, configData):
        """Create or change a registry entry from raw configuration
        data.

	The parameters specify the entry contents:

	* `path`: The path to the entry. The parent entry must already
          exist. If a subentry with the given name (the last component
          in the path) does not already exist under the parent, a new
          one will be created. Otherwise, the contents of the
          previously exiting entry will be completely replaced (but
          not its subentries!). This means that names are guaranteed
          to be unique in a particular node.
	* `backend`: An arbitrary string identifying the RelRDF backend 
	  this antry applies to, e.g., ``"postgres"``.
	* `version`: A positive integer identifying the version of the
          configuration data format used by the backend. This can be
          used by backends to mark backwards-incompatible format
          changes, so that older versions can simply reject to read
          data created by newer ones in backwards-incompatible ways.
	* `descr`: Arbitrary, descriptive text for the entry, usually
	  provided by the user creating the entry.
	* `configData`: Configuration data for the entry. This is an
	  arbitrary Python object that must be serializable using the
	  standard :mod:`json` module. The actual contents of this
	  object are backend-dependent and will normally be obtained
	  by parsing e.g., a command-line specification using a
	  backend-specific function. This class will only store and
	  retrieve the configuration data object without trying to
	  interpret it in any way.
	"""
        assert len(path) > 0
        assert isinstance(backend, basestring)
        assert isinstance(version, int) and version > 0
        assert isinstance(descr, basestring)

        self._loadData()

        node = self._getNode(path[:-1])

        entries = node.get('entries')
        if entries is None:
            entries = {}
            node['entries'] = entries

        entries[path[-1]] = {
            'backend': backend,
            'version': version,
            'descr': descr,
            'configData': configData,
            }

        self._saveData()

    def setEntry(self, path, descr, config):
        """Create or change a registry entry.

	The parameters specify the entry contents:

	* `path`: The path to the entry. The parent entry must already
          exist. If a subentry with the given name (the last component
          in the path) does not already exist under the parent, a new
          one will be created. Otherwise, the contents of the
          previously exiting entry will be completely replaced (but
          not its subentries!). This means that names are guaranteed
          to be unique in a particular node.
	* `descr`: Arbitrary, descriptive text for the entry, usually
	  provided by the user creating the entry.
	* `config`: A configuration object encapsulating the modelbase
	  configuration. It is expected to be an instance of
	  :class:`ModelbaseConfig`.
	"""
        backend, version, configData = config.freeze()
        self.setRawEntry(path, backend, version, descr, configData)

    def setDefaultEntry(self, path):
        """
	Make the entry with path `path` the default entry for its
        parent entry. If the last component of `path` is ``None``, the
        parent entry will have no default subentry from this point on.

	If the specified entry does not already exist in the registry,
	a :exc:`ConfigurationError` will be raised.
	"""
        assert len(path) > 0

        self._loadData()

        node = self._getNode(path[:-1])
        name = path[-1]

        entries = node.get('entries')
        defNode = entries is not None and entries.get(name)
        
        if name not in entries:
            raise ConfigurationError(
                _("Specified default entry '%s' does not exist") % name)
        node['default'] = name

        self._saveData()

    def getEntryNames(self, path):
        """
	Return a sequence (iterable) with all subentry names for the
        entry identified by `path`, in no particular order.

	The behavior of the returned iterator is undefined if the
	registry is changed while iteration is still in progress.
	"""
        node = self._getNode(path)
        entries = node.get('entries') or {}
        return entries.iterkeys()

    def getDefaultName(self, path):
        """
	Return the name of the current default subentry for the entry
        identified by `path`, or `None` if no default entry is
        currently set.
	"""
        node = self._getNode(path)
        return node.get('default')

    def getRawEntry(self, path):
        """Retrieve the raw contents of an entry.

	`path` identifies the entry to be retrieved.

	The return value is a tuple of the form ``(backend, version,
	descr, configData)``.  This tuple's components correspond to
	the values of the similarly-named parameters given to the
	:meth:`setRawEntry` method while creating the entry.

	Raises a :exc:`ConfigurationError` if the specified entry does
	not exist in the registry.
	"""
        node = self._getNode(path)
        return (node['backend'], node['version'], node['descr'],
                node['configData'],)

    def getEntry(self, path):
        """Retrieve the contents of an entry.

	`path` identifies the entry to be retrieved.

	The return value is a tuple of the form ``(descr,
	config)``.  This tuples's components correspond to 
	the values of the similarly-named parameters given to the
	:meth:`setEntry` method while creating the entry.

	Raises a :exc:`ConfigurationError` if the specified entry does
	not exist in the registry.
	"""
        backend, version, descr, configData = self.getRawEntry(path)
        config = modelbasefactory.thawModelbaseConfig(backend, version,
                                                      configData)
        return (descr, config)

    def removeEntry(self, path):
        """
	Remove the entry identified by `path` from the registry and
        all of its subentries.

	Raises a :exc:`ConfigurationError` if the specified entry does
	not exist in the registry.
	"""
        assert len(path) > 0

        self._loadData()

        # Retrieve the node to be deleted. This is done only to
        # guarantee that it exists.
        node = self._getNode(path)

        parentNode = self._getNode(path[:-1])
        name = path[-1]

        del parentNode['entries'][name]

        if name == parentNode.get('default'):
            parentNode['default'] = None

        self._saveData()

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
        _defaultRegistry = Registry()

    return _defaultRegistry
