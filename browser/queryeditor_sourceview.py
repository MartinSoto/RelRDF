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
        lang = lm.get_language_from_mime_type('text/x-serql')
        self.buffer.set_language(lang)
    
        super(BasicQueryEditor, self).__init__(self.buffer)

        self.set_property('tabs-width', 4)
        self.set_property('insert-spaces-instead-of-tabs', True)
        self.set_property('auto-indent', True)

	fontDescr = pango.FontDescription('monospace 12')
        if fontDescr is not None:
            self.modify_font(fontDescr)
