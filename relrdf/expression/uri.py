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


from uuid import uuid3, uuid4

from urlparse import urljoin

# Prefix to use for blank nodes
BLANK_NODE_NS = "bnode:"
BLANK_NODE_NS_UUID = uuid4()


class Uri(unicode):
    __slots__ = ()

    def __add__(self, string):
        return Uri(super(Uri, self).__add__(string))

    def isBlank(self):
        return self.startswith(BLANK_NODE_NS)

def isBlank(obj):
    return isinstance(obj, Uri) and obj.isBlank()

def newBlank():
    return Uri(BLANK_NODE_NS + unicode(uuid4()))

def newBlankFromName(name):
    uuid = uuid3(BLANK_NODE_NS_UUID, name)
    return Uri(BLANK_NODE_NS + unicode(uuid))

class Namespace(Uri):
    __slots__ = ()

    def __getitem__(self, localPart):
        # FIXME: Do we have to check for reserved URI characters here?
        return self + localPart

    #def __unicode__(self):
    #    return unicode(super(Namespace, self))

    def __getattr__(self, localPart):
        # For some strange reason, Python 2.5 searches for the
        # __unicode__ method in the object and ends up calling the
        # __getattr__ method for it. We filter everything that looks
        # similar to a special method name.
        if localPart.startswith('__'):
            raise AttributeError

        return self + localPart

    def getLocal(self, uri):
        return urljoin(self, uri)

if __name__ == '__main__':
    n1 = Namespace(u'http://www.v-modell-xt.de/schema/1#')
    n2 = Namespace(n1)
