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

import sys

from relrdf.presentation import docgen
from relrdf.presentation.docgen import nsshortener


class StaticGenerator(docgen.ContextObject):
    __slots__ = ('model',
                 'shortener',
                 'pending',
                 'generated')

    def getResFile(self, resUri):
        return self.shortener.shortenUri(resUri) + '.html'

    def renderStream(self, stream, file):
        file.write("<?xml version='1.0' encoding='iso-8859-1'?>\n")
        file.write(stream.render(method = 'xhtml', encoding='iso-8859-1'))

    def genMainPage(self):
        fileName = 'index.html'
        print '*** Generating %s' % fileName,

        generator = self.context.mainPageDsp

        outFile = self.context.fileGenerator.openGenFile(fileName)

        try:
            stream = generator.displayVrt()
            self.renderStream(stream, outFile)
            print
        except Exception, e:
            print 'Failed!'
            print >> sys.stderr, "Failed generating file '%s'" % fileName

        outFile.close()

    def genResDescr(self, resUri):
        res = self.model.load(resUri)
        if res is None:
            print '--- Resource %s not found' % resUri
            return

        fileName = self.getResFile(resUri)

        generatedCnt = len(self.generated)
        pendingCnt = len(self.pending)
        print '*** Generating %s (expected: %d, pending %d (%d%%))' % \
            (fileName, generatedCnt + pendingCnt, pendingCnt,
             (float(pendingCnt) / (generatedCnt + pendingCnt + 1)) * 100),

        generator = self.context.resPageDsp

        outFile = self.context.fileGenerator.openGenFile(fileName)

        try:
            stream = generator.displayVrt(model=self.model, res=res)
            self.renderStream(stream, outFile)
            print
        except Exception, e:
            print 'Failed!'
            print >> sys.stderr, "Failed generating file '%s'" % fileName
            raise

        outFile.close()

    def genResDescrs(self):
        from displayconf import vmxt, vmxti

        self.pending.add(vmxti.root)

        while len(self.pending) > 0:
            resUri = self.pending.pop()
            self.generated.add(resUri)

            # This indirectly calls resLink when generating links,
            # which in turns add elements to self.pending if
            # necessary.
            self.genResDescr(resUri)

    def navPageLink(self, pos):
        return 'navigation%d.html' % (pos + 1)

    def genNavLists(self):
        generator = self.context.navPage

        for i, (queryName, query) in enumerate(self.context.navQueries):
            fileName = self.navPageLink(i)
            print '*** Generating %s' % fileName,

            outFile = self.context.fileGenerator.openGenFile(fileName)

            try:
                resSet = self.model.query(query)
                stream = generator.displayVrt(model=self.model,
                                              resList=resSet.values())
                self.renderStream(stream, outFile)
                print
            except Exception, e:
                print 'Failed!'
                print >> sys.stderr, "Failed generating file '%s'" % fileName
                raise

            outFile.close()

        generator = self.context.navIndex

        fileName = 'navigation_elements.html'
        print '*** Generating %s' % fileName,

        outFile = self.context.fileGenerator.openGenFile(fileName)

        try:
            stream = generator.displayVrt()
            self.renderStream(stream, outFile)
            print
        except Exception, e:
            print 'Failed!'
            print >> sys.stderr, "Failed generating file '%s'" % fileName

        outFile.close()

    def copyBoilerplate(self):
        self.context.fileGenerator.copyStaticFile('main.css', 'css/main.css')
        self.context.fileGenerator.copyStaticFile('images/iese_logo.gif')

    def generate(self):
        self.model = self.context.model
        self.shortener = nsshortener.getPrefixes(self.model)

        self.pending = set()
        self.generated = set()

        self.copyBoilerplate()
        self.genMainPage()
        self.genNavLists()
        #self.genResDescrs()
        from displayconf import vmxti
        self.genResDescr(vmxti.root)
        self.genResDescr(vmxti.id180e3f685107411)

    def resLink(self, resUri):
        """Generate a link URL from a resource URI."""
        if resUri not in self.generated:
            self.pending.add(resUri)
        return self.getResFile(resUri)

