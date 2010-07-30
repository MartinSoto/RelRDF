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


import gtk

_classXpm = [
    "20 20 257 2",
    "  	c None",
    ". 	c #000000",
    "+ 	c #000055",
    "@ 	c #0000AA",
    "# 	c #0000FF",
    "$ 	c #002400",
    "% 	c #002455",
    "& 	c #0024AA",
    "* 	c #0024FF",
    "= 	c #004900",
    "- 	c #004955",
    "; 	c #0049AA",
    "> 	c #0049FF",
    ", 	c #006D00",
    "' 	c #006D55",
    ") 	c #006DAA",
    "! 	c #006DFF",
    "~ 	c #009200",
    "{ 	c #009255",
    "] 	c #0092AA",
    "^ 	c #0092FF",
    "/ 	c #00B600",
    "( 	c #00B655",
    "_ 	c #00B6AA",
    ": 	c #00B6FF",
    "< 	c #00DB00",
    "[ 	c #00DB55",
    "} 	c #00DBAA",
    "| 	c #00DBFF",
    "1 	c #FFFFFF",
    "2 	c #00FF55",
    "3 	c #00FFAA",
    "4 	c #00FFFF",
    "5 	c #240000",
    "6 	c #240055",
    "7 	c #2400AA",
    "8 	c #2400FF",
    "9 	c #242400",
    "0 	c #242455",
    "a 	c #2424AA",
    "b 	c #2424FF",
    "c 	c #244900",
    "d 	c #244955",
    "e 	c #2449AA",
    "f 	c #2449FF",
    "g 	c #246D00",
    "h 	c #246D55",
    "i 	c #246DAA",
    "j 	c #246DFF",
    "k 	c #249200",
    "l 	c #249255",
    "m 	c #2492AA",
    "n 	c #2492FF",
    "o 	c #24B600",
    "p 	c #24B655",
    "q 	c #24B6AA",
    "r 	c #24B6FF",
    "s 	c #24DB00",
    "t 	c #24DB55",
    "u 	c #24DBAA",
    "v 	c #24DBFF",
    "w 	c #24FF00",
    "x 	c #24FF55",
    "y 	c #24FFAA",
    "z 	c #24FFFF",
    "A 	c #490000",
    "B 	c #490055",
    "C 	c #4900AA",
    "D 	c #4900FF",
    "E 	c #492400",
    "F 	c #492455",
    "G 	c #4924AA",
    "H 	c #4924FF",
    "I 	c #494900",
    "J 	c #494955",
    "K 	c #4949AA",
    "L 	c #4949FF",
    "M 	c #496D00",
    "N 	c #496D55",
    "O 	c #496DAA",
    "P 	c #496DFF",
    "Q 	c #499200",
    "R 	c #499255",
    "S 	c #4992AA",
    "T 	c #4992FF",
    "U 	c #49B600",
    "V 	c #49B655",
    "W 	c #49B6AA",
    "X 	c #49B6FF",
    "Y 	c #49DB00",
    "Z 	c #49DB55",
    "` 	c #49DBAA",
    " .	c #49DBFF",
    "..	c #49FF00",
    "+.	c #49FF55",
    "@.	c #49FFAA",
    "#.	c #49FFFF",
    "$.	c #6D0000",
    "%.	c #6D0055",
    "&.	c #6D00AA",
    "*.	c #6D00FF",
    "=.	c #6D2400",
    "-.	c #6D2455",
    ";.	c #6D24AA",
    ">.	c #6D24FF",
    ",.	c #6D4900",
    "'.	c #6D4955",
    ").	c #6D49AA",
    "!.	c #6D49FF",
    "~.	c #6D6D00",
    "{.	c #6D6D55",
    "].	c #6D6DAA",
    "^.	c #6D6DFF",
    "/.	c #6D9200",
    "(.	c #6D9255",
    "_.	c #6D92AA",
    ":.	c #6D92FF",
    "<.	c #6DB600",
    "[.	c #6DB655",
    "}.	c #6DB6AA",
    "|.	c #6DB6FF",
    "1.	c #6DDB00",
    "2.	c #6DDB55",
    "3.	c #6DDBAA",
    "4.	c #6DDBFF",
    "5.	c #6DFF00",
    "6.	c #6DFF55",
    "7.	c #6DFFAA",
    "8.	c #6DFFFF",
    "9.	c #920000",
    "0.	c #920055",
    "a.	c #9200AA",
    "b.	c #9200FF",
    "c.	c #922400",
    "d.	c #922455",
    "e.	c #9224AA",
    "f.	c #9224FF",
    "g.	c #924900",
    "h.	c #924955",
    "i.	c #9249AA",
    "j.	c #9249FF",
    "k.	c #926D00",
    "l.	c #926D55",
    "m.	c #926DAA",
    "n.	c #926DFF",
    "o.	c #929200",
    "p.	c #929255",
    "q.	c #9292AA",
    "r.	c #9292FF",
    "s.	c #92B600",
    "t.	c #92B655",
    "u.	c #92B6AA",
    "v.	c #92B6FF",
    "w.	c #92DB00",
    "x.	c #92DB55",
    "y.	c #92DBAA",
    "z.	c #92DBFF",
    "A.	c #92FF00",
    "B.	c #92FF55",
    "C.	c #92FFAA",
    "D.	c #92FFFF",
    "E.	c #B60000",
    "F.	c #B60055",
    "G.	c #B600AA",
    "H.	c #B600FF",
    "I.	c #B62400",
    "J.	c #B62455",
    "K.	c #B624AA",
    "L.	c #B624FF",
    "M.	c #B64900",
    "N.	c #B64955",
    "O.	c #B649AA",
    "P.	c #B649FF",
    "Q.	c #B66D00",
    "R.	c #B66D55",
    "S.	c #B66DAA",
    "T.	c #B66DFF",
    "U.	c #B69200",
    "V.	c #B69255",
    "W.	c #B692AA",
    "X.	c #B692FF",
    "Y.	c #B6B600",
    "Z.	c #B6B655",
    "`.	c #B6B6AA",
    " +	c #B6B6FF",
    ".+	c #B6DB00",
    "++	c #B6DB55",
    "@+	c #B6DBAA",
    "#+	c #B6DBFF",
    "$+	c #B6FF00",
    "%+	c #B6FF55",
    "&+	c #B6FFAA",
    "*+	c #B6FFFF",
    "=+	c #DB0000",
    "-+	c #DB0055",
    ";+	c #DB00AA",
    ">+	c #DB00FF",
    ",+	c #DB2400",
    "'+	c #DB2455",
    ")+	c #DB24AA",
    "!+	c #DB24FF",
    "~+	c #DB4900",
    "{+	c #DB4955",
    "]+	c #DB49AA",
    "^+	c #DB49FF",
    "/+	c #DB6D00",
    "(+	c #DB6D55",
    "_+	c #DB6DAA",
    ":+	c #DB6DFF",
    "<+	c #DB9200",
    "[+	c #DB9255",
    "}+	c #DB92AA",
    "|+	c #DB92FF",
    "1+	c #DBB600",
    "2+	c #DBB655",
    "3+	c #DBB6AA",
    "4+	c #DBB6FF",
    "5+	c #DBDB00",
    "6+	c #DBDB55",
    "7+	c #DBDBAA",
    "8+	c #DBDBFF",
    "9+	c #DBFF00",
    "0+	c #DBFF55",
    "a+	c #DBFFAA",
    "b+	c #DBFFFF",
    "c+	c #FF0000",
    "d+	c #FF0055",
    "e+	c #FF00AA",
    "f+	c #FF00FF",
    "g+	c #FF2400",
    "h+	c #FF2455",
    "i+	c #FF24AA",
    "j+	c #FF24FF",
    "k+	c #FF4900",
    "l+	c #FF4955",
    "m+	c #FF49AA",
    "n+	c #FF49FF",
    "o+	c #FF6D00",
    "p+	c #FF6D55",
    "q+	c #FF6DAA",
    "r+	c #FF6DFF",
    "s+	c #FF9200",
    "t+	c #FF9255",
    "u+	c #FF92AA",
    "v+	c #FF92FF",
    "w+	c #FFB600",
    "x+	c #FFB655",
    "y+	c #FFB6AA",
    "z+	c #FFB6FF",
    "A+	c #FFDB00",
    "B+	c #FFDB55",
    "C+	c #FFDBAA",
    "D+	c #FFDBFF",
    "E+	c #FFFF00",
    "F+	c #FFFF55",
    "G+	c #FFFFAA",
    "H+	c #FFFFFF",
    "                                        ",
    "                                        ",
    "                                        ",
    "                                        ",
    "            8+S R h R R 8+              ",
    "          u.l (.[.[.}.(.l u.            ",
    "        }.l t.@+@+7+@+u.t.h }.          ",
    "      7+l [.@+H+H+H+H+H+@+[.h 7+        ",
    "      R (.y.H+H+@+u.@+H+b+t.(.[.        ",
    "      R R `.H+8+(.(.(.[.(.[.(.R         ",
    "      l N u.H+#+h h l h l R R h         ",
    "      R R }.H+b+R l R u.#+R R R         ",
    "      (.R R H+H+@+}.u.H+H+R R }.        ",
    "      8+h R [.8+H+H+H+b+u.R h 8+        ",
    "        }.h R (.t.u.t.(.R h [.          ",
    "          u.h R R R R R h u.            ",
    "            7+R R R R R 8+              ",
    "                                        ",
    "                                        ",
    "                                        "
    ]
classPixbuf = gtk.gdk.pixbuf_new_from_xpm_data(_classXpm)

