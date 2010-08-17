# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2010 Fraunhofer-Institut fuer Experimentelles
#                         Software Engineering (IESE).
#
# RelRDF is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

"""Generic 'diff'-style comparison routines.
"""

import difflib
import itertools


def segmentDiff(old, new):
    old = list(old)
    new = list(new)
    s = difflib.SequenceMatcher(None, new, old)

    for opcode, j1, j2, i1, i2 in s.get_opcodes():
        if opcode == 'equal':
            yield ('unmodif', new[j1:j2])
        elif opcode == 'insert':
            yield ('deleted', old[i1:i2])
        elif opcode == 'delete':
            yield ('inserted', new[j1:j2])
        elif opcode == 'replace':
            yield ('deleted', old[i1:i2])
            yield ('inserted', new[j1:j2])


def diff(old, new):
    old = list(old)
    new = list(new)
    s = difflib.SequenceMatcher(None, new, old)

    for opcode, j1, j2, i1, i2 in s.get_opcodes():
        if opcode == 'equal':
            yield ('unmodif', i1, i2, j1, j2)
        elif opcode == 'insert':
            yield ('deleted', i1, i2, j1, j2)
        elif opcode == 'delete':
            yield ('inserted', i1, i2, j1, j2)
        elif opcode == 'replace':
            yield ('deleted', i1, i2, j1, j1)
            yield ('inserted', i2, i2, j1, j2)

def diff3(orig, seqA, seqB):
    # We iterate over two comparisons at the same time. In order to
    # find the end without having our loop broken by a StopIteration
    # exception, we have some fun with the iterators first.
    endMarker = (None, None, None, None, None)
    sA = itertools.chain(diff(orig, seqA),
                         itertools.repeat(endMarker, 1))
    sB = itertools.chain(diff(orig, seqB),
                         itertools.repeat(endMarker, 1))

    # Consume both comparisons "in parallel", subdividing and
    # interleaving segments as necessary. The algorithm can be viewed
    # as follows: Each one of the two comparisons determines a
    # partition of the `orig` sequence into segments that are either
    # 'deleted' or 'unmodif'. 'inserted' segments from either `seqA`
    # or `seqB` get interspersed every now and then. We merge the two
    # partitions of `orig` producing a single partition that has a
    # segment endpoint wherever either of the two original partitions
    # had a segment endpoint. Insertions can be interspersed in this
    # partition at the same places they where originally. This is
    # always possible since the resulting partition necessarily has
    # endpoints at those places.

    # The current segments in each comparison.
    opcodeA, i1A, i2A, j1A, j2A = sA.next()
    opcodeB, i1B, i2B, j1B, j2B = sB.next()

    # The current position. It always marks the start of the next
    # segment that will be yielded.
    i = 0

    # This loop terminates since every iteration consumes at least a
    # segment from one of the comparisons.
    while opcodeA is not None or opcodeB is not None:
        # When an insertion is found, the current point is necessarily
        # at its position. We just have to output it and continue.
        if opcodeA == 'inserted':
            assert i == i1A
            yield ('insertedA', seqA[j1A:j2A])
            opcodeA, i1A, i2A, j1A, j2A = sA.next()
            continue
        if opcodeB == 'inserted':
            assert i == i1B
            yield ('insertedB', seqB[j1B:j2B])
            opcodeB, i1B, i2B, j1B, j2B = sB.next()
            continue

        # The state determines what is happening now in the
        # consolidated comparison.
        if opcodeA is None or opcodeA == 'unmodif':
            if opcodeB is None or opcodeB == 'unmodif':
                state = 'unmodif'
            else:
                state = 'deletedB'
        else:
            if opcodeB is None or opcodeB == 'unmodif':
                state = 'deletedA'
            else:
                state = 'deletedAB'

        if i2A == i2B:
            # The current segments end at the same position. Consume
            # both of them.
            yield (state, orig[i:i2A])
            i = i2A
            opcodeA, i1A, i2A, j1A, j2A = sA.next()
            opcodeB, i1B, i2B, j1B, j2B = sB.next()
        elif i2B is None or (i2A is not None and i2A < i2B):
            # Either `seqB` is exhausted, or the current A segment
            # ends first.
            yield (state, orig[i:i2A])
            i = i2A
            opcodeA, i1A, i2A, j1A, j2A = sA.next()
        else:
            # Either `seqA` is exhausted, or the current B segment
            # ends first.
            yield (state, orig[i:i2B])
            i = i2B
            opcodeB, i1B, i2B, j1B, j2B = sB.next()

