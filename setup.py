from setuptools import setup, find_packages

setup(name = 'RelRDF',
      version = '0.1',
      author = 'Martin Soto',
      author_email = 'Martin.Soto@iese.fraunhofer.de',
      url = 'http://www.iese.fraunhofer.de/',

      py_modules = ['antlr'],
      packages = find_packages(),
      scripts = ['bin/mbcleanup',
                 'bin/modelexport',
                 'bin/modelimport',
                 ],
      include_package_data = True,
     )
