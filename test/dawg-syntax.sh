#!/bin/sh
PYTHONPATH="$PYTHONPATH:../.." python2.5 dawg.py data-r2/manifest-syntax.ttl syntax_ref.log $*

