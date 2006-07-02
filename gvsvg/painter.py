import math

import units
import font


def length(l):
    return '%0.3f' % (l * units.TO_POINTS)


class SVGPainter(object):
    __slots__ = ('strm',
                 'width',
                 'height')

    def __init__(self, strm):
        self.strm = strm

    def _transform(self, x, y):
        return length(x), length(self.height - y)

    def getFont(self, fontDesc):
        return font.getFont(fontDesc)

    def open(self, width, height):
        self.width = width
        self.height = height
        self.strm.write(
'''<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN"
 "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd" [
 <!ATTLIST svg xmlns:xlink CDATA #FIXED "http://www.w3.org/1999/xlink">
]>
<svg width="%spt" height="%spt"
 viewBox = "0 0 %s %s"
 xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
''' % (length(width), length(height), length(width), length(height)))

    def _makeAttrs(self, attrs):
        return ' '.join('%s="%s"' % (name.replace('_', '-'), val)
                        for name, val in attrs.items())

    def polygon(self, points, **attrs):
        pointLst = ' '.join('%s,%s' % self._transform(*p)
                            for p in points)
        self.strm.write('<polygon points="%s" %s/>\n' %
                        (pointLst, self._makeAttrs(attrs)))

    def ellipse(self, (cx, cy), rx, ry, **attrs):
        cx, cy = self._transform(cx, cy)
        self.strm.write('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" %s/>' %
                        (cx, cy, length(rx), length(ry),
                         self._makeAttrs(attrs)))

    def openPath(self, **attrs):
        self.strm.write('<path %s d="' % self._makeAttrs(attrs))

    def moveTo(self, (x, y)):
        self.strm.write('M%s,%s' % self._transform(x, y))

    def curveTo(self, (cx1, cy1), (cx2, cy2), (x, y)):
        cx1, cy1 = self._transform(cx1, cy1)
        cx2, cy2 = self._transform(cx2, cy2)
        x, y = self._transform(x, y)
        self.strm.write('C%s,%s %s,%s %s,%s' % (cx1, cy1, cx2, cy2, x, y))

    def closePath(self):
        self.strm.write('"/>\n')

    def arrowHead(self, (x0, y0), (x1, y1), **attrs):
        x0, y0, x1, y1 = [l * units.TO_POINTS for l in x0, y0, x1, y1]
        scaleFactor = math.hypot(y1-y0, x0-x1)
        angle = math.degrees(math.atan2(y1-y0, x0-x1))

        x1, y1 = self._transform(x1, y1)
        self.strm.write('<polygon '
                        'transform="translate(%s,%s) rotate(%0.3f) '
                        'scale(%0.3f)" points="0,0 1,0.25 1,-0.25" %s/>\n' %
                        (x1, y1, angle, scaleFactor,
                         self._makeAttrs(attrs)))

    def text(self, (x, y), text, **attrs):
        x, y = self._transform(x, y)
        self.strm.write('<text text-anchor="middle" x="%s" y="%s" %s>%s'
                        '</text>\n' %
                        (x, y,
                         self._makeAttrs(attrs),
                         unicode(text).encode('utf-8')))

    def close(self):
        self.strm.write('</svg>\n')
