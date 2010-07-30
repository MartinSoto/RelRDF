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


class DependenciesMissing(Exception):
    pass

# Use the best available query editor.
try:
    from queryeditor_sourceview import BasicQueryEditor
except DependenciesMissing:
    from queryeditor_gtk import BasicQueryEditor


class QueryEditor(BasicQueryEditor):

    __slots__ = ()

    def getQueryString(self):
        buffer = self.get_buffer()
        return unicode(buffer.get_text(buffer.get_start_iter(),
                                       buffer.get_end_iter()),
                       'utf-8')

    def setQueryString(self, queryString):
        self.get_buffer().set_text(queryString.encode('utf-8'))

    @staticmethod
    def _getIterAtPos(buffer, line, col):
        # Make sure the line exists.
        if line >= buffer.get_line_count():
            line = buffer.get_line_count() - 1

        # Get a text iterator at the beginning of that line.
        itr = buffer.get_iter_at_line(line)

        # Get the line length.
        itr.forward_to_line_end()
        length = itr.get_line_offset()

        if col < length:
            itr.backward_chars(length - col)

        return itr

    def markErrorExtents(self, extents):
        """Mark the region delimited by the given extents object as an
        error in the query editor.
        """
        buffer = self.get_buffer()
        insert = buffer.get_insert()
        sel = buffer.get_selection_bound()

        # The text buffer causes a program crash if any attempt is
        # made to get text uterators out of the text bounds. We use
        # _getIterAtPos to prevent this.

        if extents.startLine is not None and \
           extents.startColumn is not None and \
           extents.endLine is not None and \
           extents.endColumn is not None:
            # Mark the exact region.
            itr = self._getIterAtPos(buffer, extents.startLine - 1,
                                     extents.startColumn - 1)
            buffer.move_mark(insert, itr)
            itr = self._getIterAtPos(buffer, extents.endLine - 1,
                                     extents.endColumn - 1)
            buffer.move_mark(sel, itr)
        elif extents.startLine is not None:
            # Mark the affected line.
            itr = self._getIterAtPos(buffer, extents.startLine - 1, 0)
            buffer.move_mark(insert, itr)
            itr.forward_to_line_end()
            buffer.move_mark(sel, itr)
        else:
            # Mark the whole query.
            itr = buffer.get_start_iter()
            buffer.move_mark(insert, itr)
            itr.forward_to_end()
            buffer.move_mark(sel, itr)

        self.scroll_mark_onscreen(insert)
        self.grab_focus()
