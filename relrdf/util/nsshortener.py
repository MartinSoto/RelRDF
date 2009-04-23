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


from relrdf import Namespace


class NamespaceUriShortener(dict):
    """Convert URIs into a shortened form using a set of namespace prefixes.

    Objects of this class are dictionaries associating namespace
    prefixes with their corresponding namespace URIs (stored as
    `Namespace` objects). Method `shortenUri` converts URIs (when
    possible) to their shortened form, using the prefixes in the set."""

    __slots__ = ('shortFmt',
                 'longFmt')

    def __init__(self, shortFmt='%s:%s', longFmt='<%s>'):
        self.shortFmt = shortFmt
        self.longFmt = longFmt

    def __setitem__(self, prefix, nsUri):
        super(NamespaceUriShortener, self).__setitem__(prefix,
                                                       Namespace(nsUri))

    addPrefix = __setitem__

    def addPrefixes(self, dict):
        """Add the prefixes in `dict` to this shortener.

        `dict` is a dictionary with prefixes as keys and namespace URIs
        as values. Existing prefixes in shortener will get clobbered
        by new definitions in `dict`."""
        for prefix, nsUri in dict.items():
            self[prefix] = nsUri

    def breakUri(self, uri):
        """Attempt to break a URI into prefix and a suffix, using the
        prefixes in this shortener.

        If a matching namespace is found, a tuple containing the
        prefix in the first position and the remaining part of the URI
        in the second position will be returned. Otherwise a tuple
        with ``None`` in the first position and `uri` in the second
        position will be returned."""

        text = unicode(uri)
        for (prefix, nsUri) in self.items():
            if text.startswith(nsUri):
                # FIXME: Check that the remaining suffix is a valid
                # XML element name.
                return (prefix, text[len(nsUri):])

        return (None, text)

    def shortenUri(self, uri):
        """Attempt to shorten a URI using the prefixes in this
        shortener.

        If a matching namespace is found, the prefix and the remaining
        part of the URI will be passed to the `shortFmt` format of
        this object to form a string. Otherwise the `longFmt` format
        of this object will be used."""

        prefix, suffix = self.breakUri(uri)
        if prefix is None:
            return self.longFmt % suffix
        else:
            return self.shortFmt % (prefix, suffix)

