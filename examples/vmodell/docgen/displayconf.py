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

# -*- coding: utf-8 -*-

import string

import xml.etree.ElementTree as et

import relrdf
from relrdf import commonns
from relrdf.expression import uri
from relrdf.util import nsshortener

from relrdf.presentation import loadres, docgen

import templates
docgen.setTemplatePath(docgen.getTemplatePath() + [templates.location])

import static

import generators
import twoway
import threeway
import navigation
from staticgen import StaticGenerator


vmxt = uri.Namespace('http://www.v-modell-xt.de/schema/1#')
vmxti = uri.Namespace('http://www.v-modell-xt.de/model/1#')


typeNames = {
    vmxt[u'Abkürzung']:
      u'Abkürzung',
    vmxt.Ablaufbaustein:
      u'Ablaufbaustein',
    vmxt.Ablaufentscheidungspunkt:
      u'Ablaufentscheidungspunkt',
    vmxt.Abschnitt:
      u'Abschnitt',
    vmxt[u'Aktivität']:
      u'Aktivität',
    vmxt[u'Aktivitätsgruppe']:
      u'Aktivitätsgruppe',
    vmxt.Begriff:
      u'Begriff',
    vmxt.Begriffsabbildung:
      u'Begriffsabbildung',
    vmxt.Bereich:
      u'Bereich',
    vmxt.Entscheidungspunkt:
      u'Entscheidungspunkt',
    vmxt[u'ErzeugendeAbhängigkeit']:
      u'Erzeugende Abhängigkeit',
    vmxt[u'ErzeugendeAbhängigkeitserweiterung']:
      u'Erzeugende Abhängigkeitserweiterung',
    vmxt[u'InhaltlicheAbhängigkeit']:
      u'Inhaltliche Abhängigkeit',
    vmxt[u'InhaltlicheAbhängigkeitserweiterung']:
      u'Inhaltliche AbhängigkeitserweiterungCompound',
    vmxt.Kapitel:
      u'Kapitel',
    vmxt.Konventionsabbildung:
      u'Konventionsabbildung',
    vmxt.Methodenreferenz:
      u'Methodenreferenz',
    vmxt.Parallelablauf:
      u'Parallelablauf',
    vmxt.ParallelablaufTeil:
      u'Parallelablaufteil',
    vmxt.Produkt:
      u'Produkt',
    vmxt.Produktgruppe:
      u'Produktgruppe',
    vmxt[u'Projektdurchführungsstrategie']:
      u'Projektdurchführungsstrategie',
    vmxt.Projektmerkmal:
      u'Projektmerkmal',
    vmxt.Projekttyp:
      u'Projekttyp',
    vmxt.Quelle:
      u'Quelle',
    vmxt.Rolle:
      u'Rolle',
    vmxt[u'Strukturabhängigkeit']:
      u'Strukturabhängigkeit',
    vmxt[u'Strukturabhängigkeitserweiterung']:
      u'Strukturabhängigkeitserweiterung',
    vmxt[u'Tailoringabhängigkeit']:
      u'Tailoringabhängigkeit',
    vmxt[u'Tailoringabhängigkeitserweiterung']:
      u'Tailoringabhängigkeitserweiterung',
    vmxt[u'Teilaktivität']:
      u'Teilaktivität',
    vmxt.Textbaustein:
      u'Textbaustein',
    vmxt.Thema:
      u'Thema',
    vmxt[u'V-Modell']:
      u'V-Modell',
    vmxt[u'V-Modell-Teil']:
      u'V-Modell-Teil',
    vmxt.Vorgehensbaustein:
      u'Vorgehensbaustein',
    vmxt.Werkzeugreferenz:
      u'Werkzeugreferenz',
    vmxt.Wert:
      u'Wert',
    }

typeSortOrder = {
    vmxt[u'Abkürzung']: 1,
    vmxt.Ablaufbaustein: 2,
    vmxt.Ablaufentscheidungspunkt: 3,
    vmxt.Abschnitt: 4,
    vmxt[u'Aktivität']: 5,
    vmxt[u'Aktivitätsgruppe']: 6,
    vmxt.Begriff: 7,
    vmxt.Begriffsabbildung: 8,
    vmxt.Bereich: 9,
    vmxt.Entscheidungspunkt: 10,
    vmxt[u'ErzeugendeAbhängigkeit']: 11,
    vmxt[u'ErzeugendeAbhängigkeitserweiterung']: 12,
    vmxt[u'InhaltlicheAbhängigkeit']: 13,
    vmxt[u'InhaltlicheAbhängigkeitserweiterung']: 14,
    vmxt.Kapitel: 15,
    vmxt.Konventionsabbildung: 16,
    vmxt.Methodenreferenz: 17,
    vmxt.Parallelablauf: 18,
    vmxt.ParallelablaufTeil: 19,
    vmxt.Produkt: 20,
    vmxt.Produktgruppe: 21,
    vmxt[u'Projektdurchführungsstrategie']: 22,
    vmxt.Projektmerkmal: 23,
    vmxt.Projekttyp: 24,
    vmxt.Quelle: 25,
    vmxt.Rolle: 26,
    vmxt[u'Strukturabhängigkeit']: 27,
    vmxt[u'Strukturabhängigkeitserweiterung']: 28,
    vmxt[u'Tailoringabhängigkeit']: 29,
    vmxt[u'Tailoringabhängigkeitserweiterung']: 30,
    vmxt[u'Teilaktivität']: 31,
    vmxt.Textbaustein: 32,
    vmxt.Thema: 33,
    vmxt[u'V-Modell']: 34,
    vmxt[u'V-Modell-Teil']: 35,
    vmxt.Vorgehensbaustein: 36,
    vmxt.Werkzeugreferenz: 37,
    vmxt.Wert: 38,
    }


ogRelNames = {
    vmxt.Ablauf:
      u'Ablauf',
    vmxt.AblaufbausteinRef:
      u'Ablaufbaustein',
    vmxt.Ablaufdarstellung:
      u'Ablaufdarstellung',
    vmxt[u'AktivitätRef']:
      u'Aktivität',
    vmxt[u'AktivitätsgruppeRef']:
      u'Aktivitätsgruppe',
    vmxt.Aufgaben_und_Befugnisse:
      u'Aufgaben und Befugnisse',
    vmxt.Begriff:
      u'Begriff',
    vmxt.BeispielProduktgestaltung:
      u'Beispiel Produktgestaltung',
    vmxt.Beispielprodukt:
      u'Beispielprodukt',
    vmxt.Beschreibung:
      u'Beschreibung',
    vmxt.Copyright_kurz:
      u'Copyright (kurz)',
    vmxt.Copyright_lang:
      u'Copyright (lang)',
    vmxt.EntscheidungspunktRef:
      u'Entscheidungspunkt',
    vmxt[u'Erläuterung']:
      u'Erläuterung',
    vmxt[u'ErweitertErzeugendeAbhängigkeitRef']:
      u'Erweitert Erzeugende Abhängigkeit',
    vmxt[u'ErweitertInhaltlicheAbhängigkeitRef']:
      u'Erweitert inhaltliche Abhängigkeit',
    vmxt[u'ErweitertStrukturabhängigkeitRef']:
      u'Erweitert Strukturabhängigkeit',
    vmxt[u'ErweitertTailoringabhängigkeitRef']:
      u'Erweitert Tailoringabhängigkeit',
    vmxt.Extern:
      u'Extern',
    vmxt.Frage:
      u'Frage',
    vmxt[u'Fähigkeitsprofil']:
      u'Fähigkeitsprofil',
    vmxt.GenerierterInhalt:
      u'Generierter Inhalt',
    vmxt.Initial:
      u'Initial',
    vmxt.MethodenreferenzRef:
      u'Methodenreferenz',
    vmxt.MitwirkenderRef:
      u'Mitwirkender',
    vmxt.NachfolgerAblaufentscheidungspunktRef:
      u'Nachfolger Ablaufentscheidungspunkt',
    vmxt.NachfolgerParallelablaufRef:
      u'Nachfolger Parallelablauf',
    vmxt.Name:
      u'Name',
    vmxt.Nummer:
      u'Nummer',
    vmxt.ProduktRef:
      u'Produkt',
    vmxt.ProduktgruppeRef:
      u'Produktgruppe',
    vmxt.Produktvorlage:
      u'Produktvorlage',
    vmxt[u'ProjektdurchführungsstrategieRef']:
      u'Projektdurchführungsstrategie',
    vmxt.ProjektmerkmalWertRef:
      u'Projektmerkmal-Wert',
    vmxt.QuelleRef:
      u'Quelle',
    vmxt.Quellenverweis:
      u'Quellenverweis',
    vmxt.Rollenbesetzung:
      u'Rollenbesetzung',
    vmxt.SchnittstellenQuellproduktRef:
      u'Schnittstellen-Quellprodukt',
    vmxt.Sinn_und_Zweck:
      u'Sinn und Zweck',
    vmxt.Text:
      u'Text',
    vmxt.TextbausteinRef:
      u'Textbaustein',
    vmxt.ThemaRef:
      u'Thema',
    vmxt.Titel:
      u'Titel',
    vmxt[u'V-Modell-Kern']:
      u'V-Modell-Kern',
    vmxt.VerantwortlicherRef:
      u'Verantwortlicher',
    vmxt.Version:
      u'Version',
    vmxt.Version_intern:
      u'Version (intern)',
    vmxt.VonProduktRef:
      u'Von Produkt',
    vmxt.VorgehensbausteinRef:
      u'Vorgehensbaustein',
    vmxt.WerkzeugreferenzRef:
      u'Werkzeugreferenz',
    vmxt.ZuProduktRef:
      u'Zu Produkt',
    vmxt.Zusammenfassung:
      u'Zusammenfassung',
    vmxt.basiert_auf_VB_Ref:
      u'Basiert auf Vorgehensbaustein',
    vmxt[u'enthält']:
      u'Teile',
    vmxt.isEnd:
      u'Is End',
    vmxt.isStart:
      u'Is Start',
    vmxt.kann_basieren_auf_VB_Ref:
      u'Kann basieren auf',
    vmxt.vielfachheit:
      u'vielfachheit',
    vmxt.wird_abgebildet_durchAGRef:
      u'Wird abgebildet durch',
    vmxt.wird_abgebildet_durchAbschnittRef:
      u'Wird abgebildet durch',
    vmxt[u'wird_abgebildet_durchAktivitätRef']:
      u'Wird abgebildet durch',
    vmxt.wird_abgebildet_durchEntscheidungspunktRef:
      u'Wird abgebildet durch',
    vmxt.wird_abgebildet_durchKapitelRef:
      u'Wird abgebildet durch',
    vmxt.wird_abgebildet_durchKonventionsabbildungRef:
      u'Wird abgebildet durch',
    vmxt.wird_abgebildet_durchMethodenreferenzRef:
      u'Wird abgebildet durch',
    vmxt.wird_abgebildet_durchPDSRef:
      u'Wird abgebildet durch',
    vmxt.wird_abgebildet_durchPGRef:
      u'Wird abgebildet durch',
    vmxt.wird_abgebildet_durchProduktRef:
      u'Wird abgebildet durch',
    vmxt.wird_abgebildet_durchRolleRef:
      u'Wird abgebildet durch',
    vmxt.wird_abgebildet_durchTeilRef:
      u'Wird abgebildet durch',
    vmxt[u'wird_abgebildet_durchTeilaktivitätRef']:
      u'Wird abgebildet durch',
    vmxt.wird_abgebildet_durchThemaRef:
      u'Wird abgebildet durch',
    vmxt.wird_abgebildet_durchVBRef:
      u'Wird abgebildet durch',
    vmxt.wird_abgebildet_durchWerkzeugr:
      u'Wird abgebildet durch',
    vmxt.wird_abgebildet_durchWerkzeugreferenzRef:
      u'Wird abgebildet durch',
    vmxt[u'Überblicksgrafik']:
      u'Überblicksgrafik',
    }


icRelNames = {
    vmxt.AblaufbausteinRef:
      u'Ablauf von',
    vmxt[u'AktivitätRef']:
      u'Teilaktivitäten',
    vmxt[u'AktivitätsgruppeRef']:
      u'Teilaktivitäten',
    vmxt.EntscheidungspunktRef:
      u'Entscheidungspunkt von',
    vmxt[u'ErweitertErzeugendeAbhängigkeitRef']:
      u'Erweitert Erzeugende Abhängigkeit von',
    vmxt[u'ErweitertInhaltlicheAbhängigkeitRef']:
      u'Erweitert inhaltliche Abhängigkeit von',
    vmxt[u'ErweitertStrukturabhängigkeitRef']:
      u'Erweitert Strukturabhängigkeit von',
    vmxt[u'ErweitertTailoringabhängigkeitRef']:
      u'Erweitert Tailoringabhängigkeit von',
    vmxt.MethodenreferenzRef:
      u'Methodenreferenz',
    vmxt.MitwirkenderRef:
      u'Mitwirkender',
    vmxt.NachfolgerAblaufentscheidungspunktRef:
      u'Nachfolger Ablaufentscheidungspunkt von',
    vmxt.NachfolgerParallelablaufRef:
      u'Nachfolger Parallelablauf von',
    vmxt.ProduktRef:
      u'Produkt von',
    vmxt.ProduktgruppeRef:
      u'Teilprodukte',
    vmxt[u'ProjektdurchführungsstrategieRef']:
      u'Projektdurchführungsstrategie von',
    vmxt.QuelleRef:
      u'Quelle von',
    vmxt.SchnittstellenQuellproduktRef:
      u'Schnittstellen-Quellprodukt',
    vmxt.TextbausteinRef:
      u'Textbaustein von',
    vmxt.ThemaRef:
      u'Thema von',
    vmxt.VerantwortlicherRef:
      u'Verantwortlicher für',
    vmxt.VonProduktRef:
      u'"Von Produkt" von',
    vmxt.VorgehensbausteinRef:
      u'Vorgehensbaustein von',
    vmxt.WerkzeugreferenzRef:
      u'Werkzeugreferenz von',
    vmxt.ZuProduktRef:
      u'"Zu Produkt" von',
    vmxt.basiert_auf_VB_Ref:
      u'Basis von',
    vmxt[u'enthält']:
      u'Teil von',
    vmxt.kann_basieren_auf_VB_Ref:
      u'Mögliche Basis für',
    vmxt.wird_abgebildet_durchAGRef:
      u'Ist Abbildung von',
    vmxt.wird_abgebildet_durchAbschnittRef:
      u'Ist Abbildung von',
    vmxt[u'wird_abgebildet_durchAktivitätRef']:
      u'Ist Abbildung von',
    vmxt.wird_abgebildet_durchEntscheidungspunktRef:
      u'Ist Abbildung von',
    vmxt.wird_abgebildet_durchKapitelRef:
      u'Ist Abbildung von',
    vmxt.wird_abgebildet_durchKonventionsabbildungRef:
      u'Ist Abbildung von',
    vmxt.wird_abgebildet_durchMethodenreferenzRef:
      u'Ist Abbildung von',
    vmxt.wird_abgebildet_durchPDSRef:
      u'Ist Abbildung von',
    vmxt.wird_abgebildet_durchPGRef:
      u'Ist Abbildung von',
    vmxt.wird_abgebildet_durchProduktRef:
      u'Ist Abbildung von',
    vmxt.wird_abgebildet_durchRolleRef:
      u'Ist Abbildung von',
    vmxt.wird_abgebildet_durchTeilRef:
      u'Ist Abbildung von',
    vmxt[u'wird_abgebildet_durchTeilaktivitätRef']:
      u'Ist Abbildung von',
    vmxt.wird_abgebildet_durchThemaRef:
      u'Ist Abbildung von',
    vmxt.wird_abgebildet_durchVBRef:
      u'Ist Abbildung von',
    vmxt.wird_abgebildet_durchWerkzeugreferenzRef:
      u'Ist Abbildung von',
    }

singleVersionQueries = [
    (u"Grundentitäten",
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       ?value1 a ?type .
       filter (?type = vmxt:V-Modell ||
               ?type = vmxt:Vorgehensbaustein ||
               ?type = vmxt:Projektdurchführungsstrategie)
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name)
     }"""),
    (u"Dokumentation",
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       ?value1 a ?type .
       filter (?type = vmxt:V-Modell-Teil)
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name)
     }"""),
    (u"Glossar",
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       ?value1 a ?type .
       filter (?type = vmxt:Abkürzung ||
               ?type = vmxt:Begriff)
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name)
     }"""),
    ]
    
twoWayQueries = singleVersionQueries + [
    (u"Neue Entitäten",
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compB {?value1 a ?type .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u"Gelöschte Entitäten",
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compA {?value1 a ?type .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u"Umbenannte Entitäten",
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compA {?value1 vmxt:Name ?val1 .}
       graph relrdf:compB {?value1 vmxt:Name ?val2 .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u'"Sinn und Zweck" geändert',
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compA {?value1 vmxt:Sinn_und_Zweck ?val1 .}
       graph relrdf:compB {?value1 vmxt:Sinn_und_Zweck ?val2 .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u'Beschreibung geändert',
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compA {?value1 vmxt:Beschreibung ?val1 .}
       graph relrdf:compB {?value1 vmxt:Beschreibung ?val2 .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u'Themenzuordnung geändert',
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       ?value1 rdf:type vmxt:Thema .
       graph relrdf:compA {?value1 vmxt:ProduktRef ?val1 .}
       graph relrdf:compB {?value1 vmxt:ProduktRef ?val2 .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u'Mitwirkende geändert',
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compA {?value1 vmxt:MitwirkenderRef ?val1 .}
       graph relrdf:compB {?value1 vmxt:MitwirkenderRef ?val2 .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u'Verantwortlicher geändert',
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compA {?value1 vmxt:VerantwortlicherRef ?val1 .}
       graph relrdf:compB {?value1 vmxt:VerantwortlicherRef ?val2 .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u'Produkte mit geänderten Themen',
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compAB {?value1 rdf:type vmxt:Produkt}
       ?t rdf:type vmxt:Thema .
       graph ?g {?t vmxt:ProduktRef ?value1}
       filter (?g = relrdf:compA ||
               ?g = relrdf:compB)
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u'"Teil von" verschoben',
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compA {?parent1 vmxt:enthält ?value1 .}
       graph relrdf:compB {?paren2 vmxt:enthält ?value1 .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u'Alle geänderten Entitäten',
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compA {?value1 ?prop ?val1 .}
       graph relrdf:compB {?value1 ?prop ?val2 .}
       ?prop rdfs:range rdfs:Literal .
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    ]
    
threeWayQueries = singleVersionQueries + [
    (u"Zwischen %(nameA)s und %(nameB)s hinzugekommene Entitäten",
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compB {?value1 a ?type .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u"Zwischen %(nameA)s und %(nameB)s hinzugekommene Entitäten "
     "(in %(nameC)s enthalten)",
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compB {?value1 a ?type .}
       graph relrdf:modelC {?cont a ?type .}
       {?cont vmxt:enthält ?value .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
#     (u"Gelöschte Entitäten",
#      u"""
#      select ?value1 ?subgraph1 ?rel1 ?value2 {
#        graph relrdf:compA {?value1 a ?type .}
#        graph ?subgraph1 {
#          ?value1 ?rel1 ?value2 .
#        }
#        filter (?rel1 = rdf:type ||
#                ?rel1 = vmxt:Name ||
#                ?rel1 = vmxt:Titel)
#      }"""),
    (u"Umbenannte in %(nameB)s (kein Konflikt)",
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compAC {?value1 vmxt:Name ?val1 .}
       graph relrdf:compB {?value1 vmxt:Name ?val2 .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u"Umbenännungskonflikte",
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compA {?value1 vmxt:Name ?val1 .}
       graph relrdf:compB {?value1 vmxt:Name ?val2 .}
       graph relrdf:compC {?value1 vmxt:Name ?val3 .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u'"Sinn und Zweck" geändert in %(nameB)s (kein Konflikt)',
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compAC {?value1 vmxt:Sinn_und_Zweck ?val1 .}
       graph relrdf:compB {?value1 vmxt:Sinn_und_Zweck ?val2 .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u'Konflikte an "Sinn und Zweck"',
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compA {?value1 vmxt:Sinn_und_Zweck ?val1 .}
       graph relrdf:compB {?value1 vmxt:Sinn_und_Zweck ?val2 .}
       graph relrdf:compC {?value1 vmxt:Sinn_und_Zweck ?val3 .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u'"Beschreibung" geändert in %(nameB)s (kein Konflikt)',
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compAC {?value1 vmxt:Beschreibung ?val1 .}
       graph relrdf:compB {?value1 vmxt:Beschreibung ?val2 .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    (u'Konflikte an "Beschreibung"',
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compA {?value1 vmxt:Beschreibung ?val1 .}
       graph relrdf:compB {?value1 vmxt:Beschreibung ?val2 .}
       graph relrdf:compC {?value1 vmxt:Beschreibung ?val3 .}
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
#     (u'Alle geänderten Entitäten (kein Konflikt)',
#      u"""
#      select ?value1 ?subgraph1 ?rel1 ?value2 {
#        graph relrdf:compAC {?value1 ?prop ?val1 .}
#        graph relrdf:compB {?value1 ?prop ?val2 .}
#        ?prop rdfs:range rdfs:Literal .
#        graph ?subgraph1 {
#          ?value1 ?rel1 ?value2 .
#        }
#        filter (?rel1 = rdf:type ||
#                ?rel1 = vmxt:Name ||
#                ?rel1 = vmxt:Titel)
#      }"""),
    (u'Alle Konflikte',
     u"""
     select ?value1 ?subgraph1 ?rel1 ?value2 {
       graph relrdf:compA {?value1 ?prop ?val1 .}
       graph relrdf:compB {?value1 ?prop ?val2 .}
       graph relrdf:compC {?value1 ?prop ?val3 .}
       ?prop rdfs:range rdfs:Literal .
       graph ?subgraph1 {
         ?value1 ?rel1 ?value2 .
       }
       filter (?rel1 = rdf:type ||
               ?rel1 = vmxt:Name ||
               ?rel1 = vmxt:Titel)
     }"""),
    ]


class BaseModelWrapper(object):
    """A wrapper for models following the V-Modell schema."""

    __slots__ = ('model',
                 'shortener',
                 'resWidget',)

    def __init__(self, model):
        self.model = model

        # Create an URI shortener for the model.
        self.shortener = nsshortener.NamespaceUriShortener(shortFmt='%s:%s',
                                                           longFmt='<%s>')
        # Standard namespaces.
        self.shortener.addPrefix('rdf', commonns.rdf)
        self.shortener.addPrefix('rdfs', commonns.rdfs)
        self.shortener.addPrefix('relrdf', commonns.relrdf)

        # Add the namespaces from the model.
        self.shortener.addPrefixes(model.getPrefixes())

        self.resWidget = None


    #
    # Model Data Extraction
    #

    _ogQuery = string.Template(u"""
        select ?value1 ?rel1 ?subgraph1 ?value2 ?rel2 ?subgraph2 ?value3
        where {
          graph ?subgraph1 {
            ?value1 ?rel1 ?value2 .
          }
          filter (?value1 = <$resUri>)
          optional {
            graph ?subgraph2 {
              ?value2 ?rel2 ?value3 .
            }
            filter (?rel2 = rdf:type ||
                    ?rel2 = vmxt:Name ||
                    ?rel2 = vmxt:Titel ||
                    ?rel2 = vmxt:Nummer)
          }
        }
        """)

    _icQuery = string.Template(u"""
        select ?value1 ?rel1 ?subgraph1 ?value2
               'value3'=?value1 ?rel3 ?subgraph3 ?value4
        where {
          graph ?subgraph1 {
            ?value1 ?rel1 ?value2 .
          }
          filter (?value2 = <$resUri>)
          optional {
            graph ?subgraph3 {
              ?value1 ?rel3 ?value4 .
            }
            filter (?rel3 = rdf:type ||
                    ?rel3 = vmxt:Name  ||
                    ?rel3 = vmxt:Titel ||
                    ?rel3 = vmxt:Nummer)
          }
        }
        """)

    def getOgRels(self, resUri):
        return self.model.query('sparql',
                                self._ogQuery.substitute(resUri=resUri))

    def getIcRels(self, resUri):
        return self.model.query('sparql',
                                self._icQuery.substitute(resUri=resUri))

    def load(self, resUri):
        resSet = loadres.ResourceSet()

        try:
            # FIXME: Writing web values into queries without protecting
            # them is a security risk.
            results = self.getOgRels(resUri)
            resSet.addResults(results)

            # FIXME: Writing web values into queries without protecting
            # them is a security risk.
            results = self.getIcRels(resUri)
        finally:
            resSet.addResults(results)

        try:
            return resSet[resUri]
        except KeyError:
            return None

    def query(self, query):
        resSet = loadres.ResourceSet()

        results = self.model.query('sparql', query)
        resSet.addResults(results)

        return resSet


    #
    # URI Shortening
    #

    def getPrefixes(self):
        return self.model.getPrefixes()

    def shortenUri(self, uri):
        if uri is not None:
            return self.shortener.shortenUri(uri)
        else:
            return None


class ModelWrapper(BaseModelWrapper):
    __slots__ = ('resSet',)

    _allQuery = u"""
        select ?value1 ?rel1 ?subgraph1 ?value2
        where {
          graph ?subgraph1 {
            ?value1 ?rel1 ?value2 .
          }
        }
        """

    def __init__(self, model, **kwargs):
        super(ModelWrapper, self).__init__(model, **kwargs)

        # Load the whole model.
        print '*** Loading model.'
        self.resSet = loadres.ResourceSet()
        results = self.model.query('sparql', self._allQuery)
        self.resSet.addResults(results)

    def load(self, resUri):
        try:
            return self.resSet[resUri]
        except KeyError:
            return None

#
# Main Title
#

@docgen.ContextFunction
def makeTitle(context):
    if 'nameA' in context and 'nameB' in context and 'nameC' in context:
        return 'RelRDF Merge: %s + %s (Vorfahren: %s)' % \
            (context.nameC, context.nameB, context.nameA)
    elif 'nameA' in context and 'nameB' in context:
        return 'RelRDF: Vergleich von %s und %s' % (context.nameA,
                                                      context.nameB)
    elif 'nameA' in context:
        return 'RelRDF: %s' % context.nameA
    else:
        return 'RelRdf'


#
# HTML Properties
#

@docgen.ContextFunction
def htmlFilter(stream, context):
    """Adapt the links in V-Modell descriptions to our structure."""
    for kind, data, pos in stream:
        if kind == 'START':
            tag, attrs = data
            if 'href' in attrs:
                newVal = context.resLink(vmxti['id' + attrs.get('href')[1:]])
                yield kind, (tag, attrs | [('href', newVal)]), pos
                continue

        yield kind, data, pos



#
# Resource List Sorting
#

@docgen.ContextFunction
def resSortKey(res, context):
   return (context.typeSortOrder.get(res.og.value(commonns.rdf.type).uri),
           int(res.og.value(vmxt.Nummer, 0)),
           res.og.value(vmxt.Name))

@docgen.ContextFunction
def filterRes(res, context):
    type = res.og.value(commonns.rdf.type)
    return type is not None and \
        context.typeSortOrder.get(type.uri) is not None


#
# Single Model Display
#

def makeSimpleConf(nameA, **kwArgs):
    generator = StaticGenerator()

    return docgen.Configuration(
        mainPageDsp = generators.MainPageDisplay(),
        resPageDsp = generators.ResourcePageDisplay(),
        resourceDsp = generators.ResourceDisplay(),

        resTypeDsp = generators.StdResTypeDisplay(),
        resNameDsp = generators.StdResNameDisplay(),

        textPropDsp = docgen.Renamer(generators.OgPropertyDisplay(),
                                     valueDsp = 'textValueDsp'),
        htmlPropDsp = docgen.Renamer(generators.OgPropertyDisplay(),
                                     valueDsp = 'htmlValueDsp'),
        ogRelPropDsp = docgen.Renamer(generators.OgPropertyDisplay(),
                                      valueDsp = 'resListDsp'),
        icRelPropDsp = docgen.Renamer(generators.IcPropertyDisplay(),
                                      valueDsp = 'resListDsp'),
        
        textValueDsp = generators.StdTextValueDisplay(),
        htmlValueDsp = generators.StdHtmlValueDisplay(),
        resListDsp = generators.StdRdfResList(),

        nameProps = (vmxt.Name, vmxt.Titel),

        typeNames = typeNames,
        typeSortOrder = typeSortOrder,

        filterRes = filterRes,
        resSortKey = resSortKey,

        ogRelNames = ogRelNames,
        icRelNames = icRelNames,

        makeTitle = makeTitle,

        htmlFilter = htmlFilter,

        navIndex = navigation.NavigationIndex(),
        navPage = navigation.NavigationPage(),

        navQueries = singleVersionQueries,

        fileGenerator = docgen.FileGenerator(),
        staticPath = [static.location],

        vmxt = vmxt,
        vmxti = vmxti,

        main = generator,
        resLink = generator.resLink,
        navPageLink = generator.navPageLink,

        nameA = nameA,
        )


#
# Two-way Model Comparison
#

def makeTwoWayConf(nameB, **kwArgs):
    config = makeSimpleConf(**kwArgs)

    config.update(
        textValueDsp = twoway.TwoWayTextValueDisplay(),
        htmlValueDsp = twoway.TwoWayHtmlValueDisplay(),
        resListDsp = twoway.TwoWayRdfResList(),

        navQueries = twoWayQueries,

        nameB = nameB,
        )

    return config


#
# Three-way Model Comparison
#

def makeThreeWayConf(nameB, nameC, **kwArgs):
    config = makeSimpleConf(**kwArgs)

    names = dict(nameA=kwArgs['nameA'], nameB=nameB, nameC=nameC)
    queries = [(queryName % names, query) for queryName, query in
               threeWayQueries]

    config.update(
        textValueDsp = threeway.ThreeWayTextValueDisplay(),
        htmlValueDsp = threeway.ThreeWayHtmlValueDisplay(),
        resListDsp = threeway.ThreeWayRdfResList(),

        navQueries = queries,

        nameB = nameB,
        nameC = nameC,
        )

    return config


#
# Configuration Factory
#

def getConfig(modelType, modelArgs, **kwArgs):
    modelType = modelType.lower()
    if modelType == 'singleversion':
        config = makeSimpleConf(**kwArgs)
    elif modelType == 'twoway':
        config = makeTwoWayConf(**kwArgs)
    elif modelType == 'threeway':
        config = makeThreeWayConf(**kwArgs)

    return config
        
