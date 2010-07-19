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


class ModelbaseConfig(object):
    """
    Interface for a modelbase configuration.

    Modelbase configurations are objects that uniquely identify a
    modelbase. The :meth:`getModelbase` method can be used to
    instantiate the actual modelbase from a configuration. The
    :meth:`thaw` and :meth:`freeze` methods can be used to "freeze" a
    configuration into a JSON-serializable form that can be stored
    persistently (see class :class:`Registry`) and to later
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


