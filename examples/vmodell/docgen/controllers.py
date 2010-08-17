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

import urllib

from relrdf.util import nsshortener
from relrdf import commonns

import turbogears
from turbogears import controllers, expose

import widgets
import displayconf
import navigation

from displayconf import vmxt, vmxti


class Root(controllers.RootController):
    """A web server for publishing V-Modell-based models.
    """

    def __init__(self, model, navElemList):
        self.model = model
        self.model.linkMaker = self

        self.resourceDsp = self.model.getResourceWidget()

        self.nav = navigation.NavElemContainer(navElemList)


    #
    # Exposed Methods
    #

    @expose(template='modpub.templates.modelnav')
    def index(self):
        return dict(resUri=urllib.quote(vmxti.root))

    @expose(template='modpub.templates.respage')
    def resDescr(self, resUri):
        return dict(model=self.model,
                    res=self.model.load(resUri),
                    resourceDsp=self.resourceDsp)


    #
    # Link Generation
    #

    def resLink(self, model, resUri):
        return 'javascript:loadRes("%s")' % urllib.quote(resUri)

