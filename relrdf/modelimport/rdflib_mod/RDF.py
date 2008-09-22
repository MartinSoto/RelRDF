# Adapted from rdflib
#
# Original copyright notice:
#
# Copyright (c) 2002, Daniel Krech, http://eikeon.com/
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
#   * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following
# disclaimer in the documentation and/or other materials provided
# with the distribution.
#
#   * Neither the name of Daniel Krech nor the names of its
# contributors may be used to endorse or promote products derived
# from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from relrdf.expression.uri import Namespace

RDFNS = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

# Syntax names
RDF = RDFNS["RDF"]
Description = RDFNS["Description"]
ID = RDFNS["ID"]
about = RDFNS["about"]
parseType = RDFNS["parseType"]
resource = RDFNS["resource"]
li = RDFNS["li"]
nodeID = RDFNS["nodeID"]
datatype = RDFNS["datatype"]

# RDF Classes
Seq = RDFNS["Seq"]
Bag = RDFNS["Bag"]
Alt = RDFNS["Alt"]
Statement = RDFNS["Statement"]
Property = RDFNS["Property"]
XMLLiteral = RDFNS["XMLLiteral"]
List = RDFNS["List"]

# RDF Properties
subject = RDFNS["subject"]
predicate = RDFNS["predicate"]
object = RDFNS["object"]
type = RDFNS["type"]
value = RDFNS["value"]
first = RDFNS["first"]
rest = RDFNS["rest"]
# and _n where n is a non-negative integer

# RDF Resources
nil = RDFNS["nil"]
