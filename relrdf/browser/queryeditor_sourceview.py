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


import gtk
import pango

import queryeditor

# Check for gtksourceview.
try:
    import gtksourceview
except ImportError:
    raise queryeditor.DependenciesMissing


class BasicQueryEditor(gtksourceview.SourceView):
    """A query editor widget based on GtkSourceView."""

    __slots__ = ('buffer',)

    def __init__(self):
	self.buffer = gtksourceview.SourceBuffer()
        self.buffer.set_property('check-brackets', True)
        self.buffer.set_property('highlight', True)

	lm = gtksourceview.SourceLanguagesManager()
        lang = lm.get_language_from_mime_type('application/sparql-query')
        self.buffer.set_language(lang)
    
        super(BasicQueryEditor, self).__init__(self.buffer)

        self.set_property('tabs-width', 4)
        self.set_property('insert-spaces-instead-of-tabs', True)
        self.set_property('auto-indent', True)

	fontDescr = pango.FontDescription('monospace 12')
        if fontDescr is not None:
            self.modify_font(fontDescr)
