#!/bin/sh
PYTHONPATH="$PYTHONPATH:../.." python2.5 dawg.py data-r2/manifest-evaluation.ttl eval_ref.log $*

