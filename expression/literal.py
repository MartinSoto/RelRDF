class Literal(unicode):
    __slots__ = ('typeUri',
                 'lang')

    def __new__(cls, value, typeUri=None, lang=None):
        self = super(Literal, cls).__new__(cls, value)

        self.typeUri = typeUri
        self.lang = lang

        return self

    def __repr__(self):
        if self.typeUri == None and self.lang == None:
            return '"%s"' % self
        elif self.typeUri != None:
            return '"%s"^^<%s>' % (self, self.typeUri)
        else:
            return '"%s"@%s' % (self, self.lang)


