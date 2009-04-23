RelRDF: A System for Storage and Comparison of RDF models
=========================================================

RelRDF is a storage system for RDF models, with support for W3C's
SPARQL query language for RDF. RelRDF was designed explicitly with the
aim of allowing for RDF model comparison. In order to compare RDF models
(or, strictly speaking, model versions) RelRDF builds a so-called
comparison model out of two model versions. This special model can
later be analyzed using standard SPARQL queries in order to identify
specific types of differences between the compared versions.

RelRDF's name comes from the fact that it uses a standard relational
database as its back end. SPARQL queries are translated into
equivalent SQL queries, which are later executed by the underlying
database system. This improves performance by making it possible for
relational query optimization to take place. Although the current
stable version is based on the MySQL database system, we are in the
process of porting it to Postgress. MySQL support is likely to be
deprecated after this port is completed.

RelRDF is written in Python, and is currently only accessible as a
Python library. We plan to add a network interface to it (probably
using W3C's SPARQL protocol) so that it can easily be accessed by
programs written in other languages.

RelRDF's main author is Martin Soto <soto@iese.fraunhofer.de>. Feel
free to contact me directly for questions and comments regarding the
system.
