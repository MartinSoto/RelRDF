class Uri(unicode):
    __slots__ = ()

    def __add__(self, string):
        return Uri(super(Uri, self).__add__(string))

class Namespace(Uri):
    __slots__ = ()

    def __getitem__(self, localPart):
        # FIXME: Do we have to check for reserved URI characters here?
        return self + localPart

    #def __unicode__(self):
    #    return unicode(super(Namespace, self))
    
    def __getattr__(self, localPart):
        # For some estrange reasom, Python 2.5 searches for the
        # __unicode__ method in the object and ends up calling the
        # __getattr__ method for it. We filter everything that looks
        # similar to a special method name.
        if localPart.startswith('__'):
            raise AttributeError

        return self + localPart

    def getLocal(self, uri):
        if uri.startswith(self):
            return uri[len(self):]
        else:
            return None


if __name__ == '__main__':
    n1 = Namespace(u'http://www.v-modell-xt.de/schema/1#')
    n2 = Namespace(n1)
