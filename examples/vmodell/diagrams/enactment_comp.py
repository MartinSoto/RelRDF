# -*- coding: utf-8 -*-
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


from relrdf.presentation import graph

from vmodell import common


def createDiagram(model, canvasModel, canvasView):
    gr = graph.Digraph()
    gr.rankdir = 'LR'

    maker = common.VModellGraphMaker(gr)

    # # Create the clusters.
    # results = model.query('sparql', """
    #     select ?cluster1 ?cluster_label1
    #            'cluster_clusterStyle1'='stroke:black;fill:white;'
    #     where {
    #       ?cluster1 rdf:type vmxt:Ablaufbaustein .
    #       ?cluster1 vmxt:Name ?cluster_label1
    #     }""")
    # maker.addResults(results)

    # # Add the nodes to the clusters.
    # results = model.query('sparql', u"""
    #     select ?cluster1 ?node1
    #     where {
    #       ?cluster1 rdf:type vmxt:Ablaufbaustein .
    #       ?cluster1 vmxt:enthält ?node1 .
    #       ?node1 rdf:type vmxt:Ablaufentscheidungspunkt
    #     }""")
    # maker.addResults(results)
    # results = model.query('sparql', u"""
    #     select ?cluster1 ?node1
    #     where {
    #       ?cluster1 rdf:type vmxt:Ablaufbaustein .
    #       ?cluster1 vmxt:enthält ?node1 .
    #       ?node1 rdf:type vmxt:Parallelablauf 
    #     }""")
    # maker.addResults(results)
    # results = model.query('sparql', u"""
    #     select ?cluster1 ?node1
    #     where {
    #       ?cluster1 rdf:type vmxt:Ablaufbaustein .
    #       ?cluster1 vmxt:enthält ?pa .
    #       ?pa rdf:type vmxt:Parallelablauf .
    #       ?pa vmxt:enthält ?node1 .
    #       ?node1 rdf:type vmxt:ParallelablaufTeil
    #     }""")
    # maker.addResults(results)


    results = model.query('sparql', u"""
        select ?comp1 ?node1 ?label1 ?oldLabel1 ?newLabel1
               'shape1'='box' 'labelLineBreakWidth1'=350
               'labelAlignment1'='left'
        where {
          graph ?comp1 {?node1 rdf:type vmxt:Ablaufentscheidungspunkt}
          optional { graph relrdf:compAB {?node1 vmxt:Name ?label1} }
          optional { graph relrdf:compA {?node1 vmxt:Name ?oldLabel1} }
          optional { graph relrdf:compB {?node1 vmxt:Name ?newLabel1} }
        }""")
    maker.addResults(results)

    results = model.query('sparql', u"""
        select ?comp1 ?node1 ?label1 ?oldLabel1 ?newLabel1
               'shape1'='parallelogram' 'labelLineBreakWidth1'=350
               'labelAlignment1'='left'
        where {
          graph ?comp1 {?node1 rdf:type vmxt:Parallelablauf}
          optional { graph relrdf:compAB {?node1 vmxt:Name ?label1} }
          optional { graph relrdf:compA {?node1 vmxt:Name ?oldLabel1} }
          optional { graph relrdf:compB {?node1 vmxt:Name ?newLabel1} }
        }""")
    maker.addResults(results)

    results = model.query('sparql', u"""
        select ?comp1 ?node1 ?label1 ?oldLabel1 ?newLabel1
               'shape1'='ellipse' 'labelLineBreakWidth1'=350
               'labelAlignment1'='left'
        where {
          graph ?comp1 {?node1 rdf:type vmxt:ParallelablaufTeil}
          optional { graph relrdf:compAB {?node1 vmxt:Name ?label1} }
          optional { graph relrdf:compA {?node1 vmxt:Name ?oldLabel1} }
          optional { graph relrdf:compB {?node1 vmxt:Name ?newLabel1} }
        }""")
    maker.addResults(results)


    results = model.query('sparql', u"""
        select ?node1 ?edge_comp 'edge_arrowsize'=3.0 ?node2
        where {
          graph ?edge_comp {?node1 vmxt:NachfolgerAblaufentscheidungspunktRef ?node2}
        }""")
    maker.addResults(results)

    results = model.query('sparql', u"""
        select ?node1 ?edge_comp 'edge_arrowsize'=3.0 ?node2
        where {
          graph ?edge_comp {?node1 vmxt:NachfolgerParallelablaufRef ?node2}
        }""")
    maker.addResults(results)

    results = model.query('sparql', u"""
        select ?node1 ?edge_comp 'edge_arrowsize'=3.0 ?node2
        where {
          ?node1 rdf:type vmxt:Parallelablauf .
          ?node2 rdf:type vmxt:ParallelablaufTeil .
          graph ?edge_comp {?node1 vmxt:enthält ?node2}
        }""")
    maker.addResults(results)

    gr.layout(graph.engines.dot, canvasModel.get_root_item(), canvasView)
