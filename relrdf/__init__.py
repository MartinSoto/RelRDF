# Put public API elements in this module:

# Error classes.
from error import *

# Result types.
from results import RESULTS_COLUMNS, RESULTS_STMTS, RESULTS_MODIF

# The basic building blocks of RDF.
from relrdf.expression.uri import Uri, Namespace
from relrdf.expression.literal import Literal

# Common namespaces.
import commonns as ns

# Factory function to create model bases. Indirectly, this gives access
# to queryable model objects.
from modelbasefactory import getModelBase
