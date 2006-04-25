from relrdf.expression import uri


"""Commonly used namespaces."""

#
# Standard XML and RDF
#

xsd = uri.Namespace('http://www.w3.org/2001/XMLSchema#')
rdf = uri.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
rdfs = uri.Namespace('http://www.w3.org/2000/01/rdf-schema#')
owl = uri.Namespace('http://www.w3.org/2002/07/owl#')


#
# SerQL
#

serql = uri.Namespace('http://www.openrdf.org/schema/serql#')


#
# RelRDF
#

relrdf = uri.Namespace('http://www.iese.fraunhofer.de/namespace/RelRDF#')
