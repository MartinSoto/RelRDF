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
        return buffer.get_text(buffer.get_start_iter(),
                               buffer.get_end_iter())

    def setQueryString(self, queryString):
        self.get_buffer().set_text(queryString)

    def markErrorExtents(self, extents):
        """Mark the region delimited by the given extents object as an
        error in the query editor."""
        buffer = self.get_buffer()
        insert = buffer.get_insert()
        sel = buffer.get_selection_bound()

        if extents.startLine is not None and \
           extents.startColumn is not None and \
           extents.endLine is not None and \
           extents.endColumn is not None:
            # Mark the exact region.
            itr = buffer.get_iter_at_line_offset(extents.startLine - 1,
                                                 extents.startColumn - 1)
            buffer.move_mark(insert, itr)
            itr = buffer.get_iter_at_line_offset(extents.endLine - 1,
                                                 extents.endColumn - 1)
            buffer.move_mark(sel, itr)
        elif extents.startLine is not None:
            # Mark the affected line.
            itr = buffer.get_iter_at_line(extents.startLine - 1)
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
