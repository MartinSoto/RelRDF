import pango
import gtk

import units


class Font(object):
    __slots__ = ('layout',
                 'cssDef',
                 'fw',
                 'fh')

    DPI = 96.0

    def __init__(self, fd):
        # PyGtk doesn't really support using Pango outside of GTK. We
        # need to do a hack to be able to access a real Pango context.
        window = gtk.Window()
        context = window.create_pango_context()

        # We have to convert back from device coordinates to
        # milimeters.
        screen = window.get_screen()
#         self.fw = float(screen.get_width_mm()) / \
#                   (float(pango.SCALE * screen.get_width()) *
#                    units.TO_MM)
#         self.fh = float(screen.get_height_mm()) / \
#                   (float(pango.SCALE * screen.get_height()) *
#                    units.TO_MM)
        self.fw = 1 / (pango.SCALE * self.DPI * units.TO_INCHES)
        self.fh = self.fw

        self._makeCssProps(fd)

        self.layout = pango.Layout(context)
        self.layout.set_font_description(fd)

    def getExtents(self, text):
        self.layout.set_text(unicode(text))
        ink, logical = self.layout.get_line(0).get_extents()
        return (logical[2] * self.fw, logical[3] * self.fh,
                pango.DESCENT(logical) * self.fh)

    _pangoStyles = {
        pango.STYLE_NORMAL: '',
        pango.STYLE_ITALIC: 'font-style:italic;',
        pango.STYLE_OBLIQUE: 'font-style:oblique;'
        }

    _pangoVariants = {
        pango.VARIANT_NORMAL: '',
        pango.VARIANT_SMALL_CAPS: 'font-variant:small-caps'
        }

    _pangoWeights = {
        pango.WEIGHT_ULTRALIGHT: 'font-weight:200',
        pango.WEIGHT_LIGHT: 'font-weight:300',
        pango.WEIGHT_NORMAL: '',
        pango.WEIGHT_BOLD: 'font-weight:700',
        pango.WEIGHT_ULTRABOLD: 'font-weight:800',
        pango.WEIGHT_HEAVY: 'font-weight:900'
        }

    _pangoStretches = {
        pango.STRETCH_ULTRA_CONDENSED: 'font-stretch:ultra-condensed',
        pango.STRETCH_EXTRA_CONDENSED: 'font-stretch:extra-condensed',	
        pango.STRETCH_CONDENSED: 'font-stretch:condensed',	
        pango.STRETCH_SEMI_CONDENSED: 'font-stretch:semi-condensed',	
        pango.STRETCH_NORMAL: '',
        pango.STRETCH_SEMI_EXPANDED: 'font-stretch:semi-expanded',	
        pango.STRETCH_EXPANDED: 'font-stretch:expanded',	
        pango.STRETCH_EXTRA_EXPANDED: 'font-stretch:extra-expanded',	
        pango.STRETCH_ULTRA_EXPANDED: 'font-stretch:ultra-expanded'
        }

    def _makeCssProps(self, fd):
        pf = fd.get_family()
        assert pf is not None
        if pf.lower() == 'sans':
            pf = 'sans-serif'
        family = 'font-family:%s;' % pf

        style = self._pangoStyles[fd.get_style()]
        variant = self._pangoVariants[fd.get_variant()]
        weight = self._pangoWeights[fd.get_weight()]
        stretch = self._pangoStretches[fd.get_stretch()]

        size = 'font-size:%0.3f;' % (fd.get_size() / pango.SCALE)

        self.cssDef = '%s%s%s%s%s%s' % (family, style, variant,
                                        weight, stretch, size)

    def getCssProps(self):
        return self.cssDef


_cachedFonts = {}

def getFont(fontDesc):
    fd = pango.FontDescription(fontDesc)
    fds = fd.to_string()

    try:
        font = _cachedFonts[fds]
    except KeyError:
        font = Font(fd)
        _cachedFonts[fds] = font

    return font

