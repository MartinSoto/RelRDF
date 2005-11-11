class Var(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class Uri(str):
    def __add__(self, string):
        return Uri(super(Uri, self).__add__(string))

    def __repr__(self):
        return "<%s>" % self


class Literal(str):
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


class Pattern(object):
    def __init__(self, subject=None, pred=None, obj=None):
        self.subject = subject
        self.pred = pred
        self.obj = obj

    def __repr__(self):
        return str((self.subject, self.pred, self.obj))


class Query(object):
    def __init__(self):
        self.vars = {}

        self.prefixes = {}

    def getVariable(self, varName):
        try:
            return self.vars[varName]
        except KeyError:
            var = Var(varName)
            self.vars[varName] = var

            return var

    def setPrefix(self, prefix, uri):
        self.prefixes[prefix] = uri

    def getPrefixUri(self, prefix):
        return self.prefixes[prefix]
        # FIXME: Produce appropriate exception.

    def getPrefixes(self):
        return self.prefixes

    def solveQName(self, qName):
        pos = qName.index(':')
        base = self.getPrefixUri(qName[:pos])
        return base + qName[pos + 1:]

