import math

import font


class SimpleShape(object):
    __slots__ = ('size',
                 'font',
                 'label',
                 'lheight')

    def layout(self, node, pntr):
        self.label = node._getProp('label')
        self.font = pntr.getFont(node._getProp('labelFont'))

        w, h, d = self.font.getExtents(self.label)
        m = h * node._getProp('labelMargin')
        self.size = (w + 2*m,h + 2*m)

        self.lheight = -h/2 + d

        self.extendSize()

        return self.size[0], self.size[1]

    def extendSize(self):
        pass

    def paint(self, node, pntr, x, y):
        w, h = self.size

        self.paintShape(node, pntr, x, y, w, h)

        pntr.text((x, y + self.lheight), self.label,
                  style=self.font.getCssProps() +
                  node._getProp('labelStyle'))


class Box(SimpleShape):
    __slots__ = ()

    def extendSize(self):
        w, h = self.size
        # FIXME: For some reason metrics arent't exact.
        self.size = (w * 1.05, h)

    def paintShape(self, node, pntr, x, y, w, h):
        pntr.polygon(((x - w / 2, y - h / 2),
                      (x - w / 2, y + h / 2),
                      (x + w / 2, y + h / 2),
                      (x + w / 2, y - h / 2),
                      (x - w / 2, y - h / 2)),
                     style=node._getProp('nodeStyle'))


class Parallelogram(SimpleShape):
    __slots__ = ()

    def extendSize(self):
        w, h = self.size
        self.size = (w / 0.6, h)

    def paintShape(self, node, pntr, x, y, w, h):
        pntr.polygon(((x - w * 0.5, y - h * 0.5),
                      (x - w * 0.3, y + h * 0.5),
                      (x + w * 0.5, y + h * 0.5),
                      (x + w * 0.3, y - h * 0.5),
                      (x - w * 0.5, y - h * 0.5)),
                     style=node._getProp('nodeStyle'))


class Ellipse(SimpleShape):
    __slots__ = ()

    C = 0.75
    WF = math.sqrt(1 + C**2)
    HF = math.sqrt(1 + 1/C**2)

    def extendSize(self):
        w, h = self.size
        self.size = (w*self.WF, h*self.HF)

    def paintShape(self, node, pntr, x, y, w, h):
        pntr.ellipse((x, y), w / 2,  h / 2,
                     style=node._getProp('nodeStyle'))


_shapeClasses = {
    'box': Box,
    'ellipse': Ellipse,
    'parallelogram': Parallelogram
    }


def getShapeFactory(shapeName):
    try:
        return _shapeClasses[str(shapeName).lower()]
    except KeyError:
        assert False, "Shape '%s' not found" % shapeName
