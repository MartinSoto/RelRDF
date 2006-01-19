class Uri(str):
    def __add__(self, string):
        return Uri(super(Uri, self).__add__(string))

    def __repr__(self):
        return "<%s>" % self


