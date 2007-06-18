# Possible result types.
RESULTS_COLUMNS = 10
RESULTS_STMTS = 11
RESULTS_MODIF = 12


class ModifResults(object):
    """A results object used to report the result of a modification
    operation."""

    __slots__ = ('affectedRows')

    def __init__(self, affectedRows):
        self.affectedRows = affectedRows

    def resultType(self):
        return RESULTS_MODIF

    length = 0

    def iterAll(self):
        # This is a generator producing the empty sequence.
        if False:
            yield None

    __iter__ = iterAll
