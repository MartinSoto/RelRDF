from distutils.core import setup
setup(name='RelRDF',
      version='0.1',
      author='Martin Soto',
      author_email='Martin.Soto@iese.fraunhofer.de',
      url='http://www.iese.fraunhofer.de/',

      py_modules=['antlr'],
      packages=['rdfcanvas',
                'rdfgv',
                'relrdf'
                'relrdfbrowser',
                'relrdf.db',
                'relrdf.db.mysql',
                'relrdf.db.sqlite',
                'relrdf.expression',
                'relrdf.mapping',
                'relrdf.modelimport',
                'relrdf.serql',
                'relrdf.sparql',
                'relrdf.typecheck',
                'relrdf.util',]
     )
