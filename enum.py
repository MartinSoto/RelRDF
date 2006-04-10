# Based on the Python recipe "True immutable symbolic enumeration with
# qualified value access"
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/413486 by
# Zoran Isailovski. This code is distributed under the Python License.

def Enum(*names):
    assert names, "Empty enums are not supported"

    class EnumClass(object):
        __slots__ = names

        def __iter__(self):
            return iter(constants)

        def __len__(self):
            return len(constants)

        def __getitem__(self, i):
            return constants[i]

        def __repr__(self):
            return 'Enum' + str(names)

        def __str__(self):
            return 'enum ' + str(constants)

    class EnumValue(object):
        __slots__ = ('__value',)

        def __init__(self, value):
            self.__value = value

        value = property(lambda self: self.__value)

        enumType = property(lambda self: EnumType)

        def __hash__(self):
            return hash(self.__value)

        def __eq__(self, other):
            if not self.enumType is other.enumType:
                return False
            return self.__value == other.__value

        def __cmp__(self, other):
            if not self.enumType is other.enumType:
                raise TypeError, \
                      "Only values from the same enum are comparable"
            return cmp(self.__value, other.__value)

        def __invert__(self):
            return constants[maximum - self.__value]

        def __nonzero__(self):
            return bool(self.__value)

        def __repr__(self):
            return str(names[self.__value])

    maximum = len(names) - 1
    constants = [None] * len(names)
    for i, each in enumerate(names):
        val = EnumValue(i)
        setattr(EnumClass, each, val)
        constants[i] = val
    constants = tuple(constants)
    EnumType = EnumClass()
    return EnumType


if __name__ == '__main__':
    print '\n*** Enum Demo ***'
    print '--- Days of week ---'
    Days = Enum('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')
    print Days
    print Days.Mo
    print Days.Fr
    print Days.Mo < Days.Fr
    print list(Days)
    for each in Days:
        print 'Day:', each
    print '--- Yes/No ---'
    Confirmation = Enum('No', 'Yes')
    answer = Confirmation.No
    print 'Your answer is not', ~answer
