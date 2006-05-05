class DependenciesMissing(Exception):
    pass

# Use the best available query editor.
try:
    from queryeditor_sourceview import *
except DependenciesMissing:
    from queryeditor_gtk import *
