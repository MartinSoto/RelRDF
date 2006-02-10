class Uri(str):
    def __add__(self, string):
        return Uri(super(Uri, self).__add__(string))

class Namespace(Uri):
    def __getitem__(self, index):
        return self + index

    def __getattr__(self, attr):
        return self + attr

