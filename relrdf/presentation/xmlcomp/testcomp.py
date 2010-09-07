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

if __name__ == '__main__':
    import sys

    import relrdf
    from relrdf import commonns
    from relrdf.factory import parseCmdLineArgs

    inst, prop = sys.argv[1:3]

    argv = list(sys.argv[3:])

    baseType, baseArgs = parseCmdLineArgs(argv, 'model base')
    modelbase = relrdf.getModelbase(baseType, **baseArgs)

    modelType, modelArgs = parseCmdLineArgs(argv, 'model')
    model = modelbase.getModel(modelType, **modelArgs)

    print inst, prop

    res = model.query('sparql', '''
                        select ?graph ?value
                        where {
                          graph ?graph {%s %s ?value}
                        }
                        ''' % (inst, prop)
                      )

    textA = None
    textB = None
    textC = None
    for graph, value in res:
        if graph == commonns.relrdf.compA:
            textA = value
        elif graph == commonns.relrdf.compB:
            textB = value
        elif graph == commonns.relrdf.compC:
            textC = value

    print xmlTextDiff3(textA, textB, textC)

    sys.exit(0)

    styledA = list(styledElems(tokenizeElem(XML('<html>%s</html>' % textA)),
                          _htmlTagsMap, _htmlBreakElems))
    styledB = list(styledElems(tokenizeElem(XML('<html>%s</html>' % textB)),
                          _htmlTagsMap, _htmlBreakElems))

    from pprint import pprint as pp

    print 'styledA:'
    pp(styledA)

    print 'styledB:'
    pp(styledB)

    rawDiff = list(diff.segmentDiff(styledA, styledB))
    print 'rawDiff:'
    pp(rawDiff)

    diff = list(diffToXml(rawDiff, _htmlDiffStyles))
    print 'Diff:'
    pp(diff)


if __name__ == '__main__':
    from pprint import pprint

    textOrig = '<p>This is, indeed, some text that we use to thest our diff4 algorithm.</p>'
    textA = '<p>This string is, some text that we use to test our diff4 algorithm.</p>'
    textB = '<p>This string is, indeed, some text that we use to verify our diff3 algorithm. We hope that it works well</p>'

    #print htmlTextDiff(textOrig, textA)
    print xmlTextDiff3(textOrig, textA, textB)


