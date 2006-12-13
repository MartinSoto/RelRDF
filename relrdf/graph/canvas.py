import gtk
import goocanvas

class RdfCanvas(object):

    def __init__(self, gr, engine):
        self.window = gtk.Window()
        self.window.set_default_size(640, 600)
        self.window.show()
        self.window.connect("delete_event", gtk.main_quit)

        vbox = gtk.VBox()
        vbox.show()
        self.window.add(vbox)

        scrolled = gtk.ScrolledWindow()
        scrolled.set_shadow_type(gtk.SHADOW_IN)
        scrolled.show()
        vbox.pack_start(scrolled, expand=True)

        hbox = gtk.HBox()
        hbox.show()
        vbox.pack_start(hbox, expand=False)

        downBt = gtk.Button('Scale Down')
        downBt.show()
        hbox.pack_start(downBt, expand=True)

        upBt = gtk.Button('Scale Up')
        upBt.show()
        hbox.pack_start(upBt, expand=True)

        self.view = goocanvas.CanvasView()
        self.view.set_size_request(600, 450)
        self.view.show()
        scrolled.add(self.view)

        model = goocanvas.CanvasModelSimple()
        self.view.set_model(model)

        self.scale = 1.0

        downBt.connect('clicked', self.scaleDown)
        upBt.connect('clicked', self.scaleUp)

        gr.layout(engine, model.get_root_item(), self.view)

    def scaleDown(self, downBt):
        if self.scale - 0.2 < 0.1:
            return
        self.scale -= 0.2
        print "New scale: %.1f" % self.scale
        self.view.set_scale(self.scale)

    def scaleUp(self, downBt):
        self.scale += 0.2
        print "New scale: %.1f" % self.scale
        self.view.set_scale(self.scale)


