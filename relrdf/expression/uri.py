class Uri(unicode):
    __slots__ = ()

    def __add__(self, string):
        return Uri(super(Uri, self).__add__(string))

class Namespace(Uri):
    __slots__ = ()

    def __getitem__(self, localPart):
        # FIXME: Do we have to check for reserved URI characters here?
        return self + localPart

    def __getattr__(self, localPart):
        return self + localPart

    def getLocal(self, uri):
        if uri.startswith(self):
            return uri[len(self):]
        else:
            return None

