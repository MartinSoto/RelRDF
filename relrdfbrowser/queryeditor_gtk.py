import gtk
import pango


class BasicQueryEditor(gtk.TextView):
    """A simple query editor based on gtk.TextView.

    Used as fall back when a better implementation is not available."""

    __slots__ = ()

    def __init__(self):
        super(BasicQueryEditor, self).__init__()

	fontDescr = pango.FontDescription('monospace 12')
        if fontDescr is not None:
            self.modify_font(fontDescr)

