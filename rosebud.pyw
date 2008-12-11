#! /usr/bin/env python

import re
import os
import sys
import pycurl
from BeautifulSoup import BeautifulSoup, NavigableString

BASE = "https://sony.wiki.per.in.iz/"
PAGE = "Technical_Overview"
DOC = "h:/docs/dev/Specifications/SONY"

HEADER = r"""\documentclass[11pt,a4paper,final]{book}
\title{Interzone Technical Review}
\author{Interzone Pty. Ltd.}
\def\templatedir{../Templates/}
\input{\templatedir header.tex}
\listoffigures
\listoftables
"""

FOOTER = r"""\input{\templatedir footer.tex}
"""

footnotes = [ None ]
columns = 0
tableColumns = 0
tableHeader = False
caption = ""
spidered = {}

#===============================================================================
class Snaffle:
    #---------------------------------------------------------------------------
    def __init__( self, url, doc ):
        self.data = ""
        self.url = url
        self.doc = doc
        self.chapters = []
        self.appendix = 0

    #---------------------------------------------------------------------------
    def retrieve( self ):
        global spidered
        if spidered.has_key( self.url ):
            print "WARNING: Already spidered", self.url
            return
        spidered[self.url] = True
        c = pycurl.Curl()
        c.setopt( pycurl.WRITEFUNCTION, self._process )
        c.setopt( pycurl.SSL_VERIFYPEER, False )
        c.setopt( pycurl.URL, self.url )
        c.perform()
        c.close()

    #---------------------------------------------------------------------------
    def download( self, source, target ):
        c = pycurl.Curl()
        c.setopt( pycurl.SSL_VERIFYPEER, False )
        c.setopt( pycurl.HEADER, False )
        c.setopt( pycurl.HTTP_TRANSFER_DECODING, False )
        c.setopt( pycurl.FOLLOWLOCATION, True )
        c.setopt( pycurl.URL, source )
        file = open( os.path.join( DOC, target ), "wb" )
        c.setopt( pycurl.FILE, file )
        c.perform()
        file.close()
        c.close()

    #---------------------------------------------------------------------------
    def decode( self):
        soup = BeautifulSoup( self.data )
        mainLabel = str( soup.li.next["href"][1:] )
        mainLabel = mainLabel.replace( "%2C", "" )
        for tag in soup.findAll( "span", attrs = { "class" : "mw-headline" } ):
            anchor = tag.parent.previous
            title = self._latexString( tag.contents[0], tag.name )
            level = tag.parent.name
            depth = -1
            if level[0] == 'h':
                depth += int( level[1] )
            head = None
            if depth == 0:
                head = self.chapters
            elif depth == 1:
                head = self.chapters[-1]["sections"]
            elif depth == 2:
                head = self.chapters[-1]["sections"][-1]["sections"]
            elif depth == 3:
                head = self.chapters[-1]["sections"][-1]["sections"][-1]["sections"]
            assert head != None
            head.append( { "name" : title, "content" : "", "sections" : [] } )
            label = mainLabel + "_" + str( anchor["name"] )
            label = label.replace( "%2C", "" )
            if depth == 0 and len( head[-1]["content"] ) == 0 :
                head[-1]["content"] += r"\label{" + mainLabel + "}\n"
            head[-1]["content"] += r"\label{" + label + "}\n"
            tag = tag.next.next
            while self._withinContents( tag.nextSibling, anchor ):
                tag = tag.nextSibling
                if isinstance( tag, NavigableString ):
                    continue
                head[-1]["content"] += self._latexFormat( tag,
                                                          head[-1]["sections"],
                                                          tag )

    #---------------------------------------------------------------------------
    def output( self ):
        file = open( os.path.join( self.doc, "sony.tex" ), "w" )
        file.write( HEADER )
        for i in xrange( 1, len( self.chapters ) + 1 ):
            if i == self.appendix:
                file.write( r"\appendix" + "\n" )
            file.write( r"\input{chapter%d.tex}" % i + "\n" )
        file.write( FOOTER )
        file.close()
        for i in xrange( 1, len( self.chapters ) + 1 ):
            chapter = self.chapters[i-1]
            file = open( os.path.join( self.doc, "chapter%d.tex" % i ), "w" )
            file.write( r"\chapter{%s}" % chapter["name"] + "\n" )
            file.write( self._processContent( chapter["content"] ) )
            for section in chapter["sections"]:
                file.write( r"\section{%s}" % section["name"] + "\n" )
                file.write( self._processContent( section["content"] ) )
                for subsection in section["sections"]:
                    file.write( r"\subsection{%s}" % subsection["name"] + "\n" )
                    file.write( self._processContent( subsection["content"] ) )
                    for subsubsection in subsection["sections"]:
                        file.write( r"\subsubsection{%s}" % subsubsection["name"] + "\n" )
                        file.write( self._processContent( subsubsection["content"] ) )
                        for omitted in subsubsection["sections"]:
                            print "WARNING: Omitting %s.%s.%s.%s.%s" % ( \
                                chapter["name"],
                                section["name"],
                                subsection["name"],
                                subsubsection["name"],
                                omitted["name"] )
            file.close()

    #---------------------------------------------------------------------------
    # private:
    #---------------------------------------------------------------------------
    def _process( self, data ):
        self.data += data

    #---------------------------------------------------------------------------
    def _withinContents( self, tag, anchor ):
        return tag != None and ( not tag.__dict__.has_key( "name" ) or \
               tag.name != anchor.name )

    #---------------------------------------------------------------------------
    def _latexString( self, data, name = "" ):
        global footnotes
        if name == 'pre':
            data = data.replace( r"&lt;", r"<" )
            data = data.replace( r"&gt;", r">" )
            return str( data )
        if name == 'listing':
            data = data.replace( r"&lt;", r"<" )
            data = data.replace( r"&gt;", r">" )
            data = data.replace( r"&#40;", "(" )
            data = data.replace( r"&#41;", ")" )
            data = data.replace( r"&#91;", "[" )
            data = data.replace( r"&#93;", "]" )
            data = data.replace( r"&#123;", "{" )
            data = data.replace( r"&#125;", "}" )
            data = data.replace( r"&quot;", "\"" )
            data = data.replace( r"&nbsp;", "" )
            return str( data )
        data = str( data ).strip( "\r\n" )
        if data.find("(APPENDIX)") != -1:
            self.appendix = len(self.chapters) + 1
        data = data.replace( r"&amp;", r"\&" )
        data = data.replace( r"&nbsp;", "" )
        data = data.replace( r"_", r"\_" )
        data = data.replace( r"#", r"\#" )
        data = data.replace( r" - ", r"---" )
        data = data.replace( r"(JAS)", r"" )
        data = data.replace( r"(JAMES)", r"" )
        data = data.replace( r"(JWO)", r"" )
        data = data.replace( r"(JACK)", r"" )
        data = data.replace( r"(MATT)", r"" )
        data = data.replace( r"(CAM)", r"" )
        data = data.replace( r"(ROB)", r"" )
        data = data.replace( r"(DAN)", r"" )
        data = data.replace( r"(APPENDIX)", r"" )
        data = data.replace( r"REF:", r"" )
        data = data.replace( r"...", r"\ldots" )
        data = data.replace( r"&lt;-&gt;", r"$\mathit{\leftrightarrow}$" )
        data = data.replace( r"&lt;-", r"$\mathit{\leftarrow}$" )
        data = data.replace( r"-&gt;", r"$\mathit{\rightarrow}$" )
        data = data.replace( r"&lt;", r"$<$" )
        data = data.replace( r"&gt;", r"$>$" )
        data = data.replace( r"%", r"\%" )

        if len( data.strip() ) == 0:
            return data

        if data.strip().find( "^" ) > 0:
            if footnotes[-1] == None:
                footnotes[-1] = "(FOOTNOTE%d)" % len( footnotes )
                data = data.replace(r"^", r"\footnote{" + "%s}" % footnotes[-1])
            else:
                data = data.replace( r"^", r"\footnotemark[\value{footnote}]" )
        elif data.strip()[0] == "^":
            footnotes[-1] = data[1:]
            footnotes.append( None )
            data = ""

        p = re.compile( "(?P<b>^|[^a-zA-Z])'(?P<m>.*?)'(?P<e>$|[^a-zA-Z])" )
        data = p.sub( "\g<b>`\g<m>'\g<e>", data )
        p = re.compile( '(?P<b>^|[^a-zA-Z])"(?P<m>.*?)"(?P<e>$|[^a-zA-Z])' )
        data = p.sub( "\g<b>``\g<m>''\g<e>", data )

        return data

    #---------------------------------------------------------------------------
    def _latexFormat( self, tag, sections, parent ):
        global columns
        global tableColumns
        global tableHeader
        global caption
        content = ""
        if isinstance( tag, NavigableString ):
            return self._latexString( tag, parent.name )
        if tag.name == "p":
            content += "\n"
        elif tag.name == "ul":
            content += r"\begin{itemize}" + "\n"
        elif tag.name == "ol":
            content += r"\begin{enumerate}" + "\n"
        elif tag.name == "li":
            content += r"\item "
        elif tag.name == "a":
            index = parent.contents.index( tag )
            page = str( tag["href"].replace( "/", "" ) )
            if index > 0:
                prev = parent.contents[index - 1]
                if str( prev ).strip()[-4:] == "REF:":
                    if page.find("redlink") != -1:
                        print "WARNING: Broken reference: ", page
                        return ""
                    label = page.replace( "%2C", "" )
                    return r"section \ref{" + label.replace( "#", "_" ) + "}" 
            if page[0:4] == 'http':
                return "%s (see \\verb!%s!)" % ( str( self._latexString( tag.contents[0], tag.name ) ),
                                                 str( tag["href"] ) )
            if page.find("redlink") != -1:
                print "WARNING: Possible reference: ", page
                return ""
            if page[0:5] == 'Image':
                target = str( tag["href"][7:] ).replace( " ", "_" )
                source = str( BASE + tag.contents[0]["src"][1:] )
                width = int( tag.contents[0]["width"] )
                height = int( tag.contents[0]["height"] )
                if width > 400:
                    height = ( height * 400 ) / width 
                    width = 400
                if height > 600:
                    width = ( width * 600 ) / height 
                    height = 600
                self.download( source, target )
                content += r"\begin{figure}[htbp]" + "\n"
                content += r"\centering" + "\n"
                if caption != "":
                    content += r"\caption{" + caption + "}\n"
                caption = ""
                content += r"\includegraphics[0px,0px]" + "[%dpx,%dpx]{" % ( width, height ) + target + "}\n"
                content += r"\end{figure}" + "\n"
                return content
            print page
            sys.stdout.flush()
            snaffle = Snaffle( BASE + page, None )
            snaffle.retrieve()
            snaffle.decode()
            sections += snaffle.chapters[1:]
            for section in snaffle.chapters[0]['sections']:
                print "WARNING: Skipped section: ", section["name"]
            return snaffle.chapters[0]["content"]
        elif tag.name == 'i':
            content += r"\emph{"
        elif tag.name == 'b':
            content += r"\textbf{"
        elif tag.name == 'tt':
            content += r"\texttt{"
        elif tag.name == 'div':
            if tag.has_key("class") and tag["class"] == "printfooter":
                return ""
            if tag.has_key("class") and tag["class"] not in [ "floatnone",
                                                              "center" ]:
                language = str( tag["class"].partition( " " )[0] )
                if language == "cpp":
                    language = "c++"
                code = self._codeFormat( tag.contents[0] )
                content += r"\begin{figure}[htbp]" + "\n"
                content += r"\centering" + "\n"
                if caption != "":
                    content += r"\caption{" + caption + "}\n"
                caption = ""
                content += r"\lstset{language=" + language + "}\n"
                content += r"\begin{lstlisting}[frame=single]" + "\n"
                content += code
                content += r"\end{lstlisting}" + "\n"
                content += r"\end{figure}" + "\n"
                return content
        elif tag.name == 'br':
            return ""
        elif tag.name == 'pre':
            content += r"\begin{figure}[htbp]" + "\n"
            content += r"\centering" + "\n"
            if caption != "":
                content += r"\caption{" + caption + "}\n"
            caption = ""
            content += r"\begin{Verbatim}[frame=single]" + "\n"
        elif tag.name == 'dl':
            content += r"\begin{description}" + "\n"
        elif tag.name == 'dt':
            content += r"\item["
        elif tag.name == 'dd':
            content += r"\item "
        elif tag.name == 'table':
            content += "\n" + r"\begin{center}" + "\n"
            content += r"\begin{longtable}{(TABLEDEF)}" + "\n"
            content += r"(CAPTION) \\" + "\n"
            content += r"\hline" + "\n"
            columns = 0
            tableColumns = 0
        elif tag.name == 'caption':
            caption = self._latexString( str( tag.contents[0] ).strip() )
            return ""
        elif tag.name == "tr":
            pass
        elif tag.name == "span":
            pass
        elif tag.name == "th":
            tableHeader = True
            if columns > 0:
                content += " & "
            content += r"\textbf{"
            columns += 1
        elif tag.name == "td":
            if columns > 0:
                content += " & "
            columns += 1
            if len( tag.contents ) > 1:
                content += r"\begin{minipage}{10cm}" + "\n"
                content += r"\vspace{3pt}" + "\n"
        else:
            print tag
            assert False
        for line in tag.contents:
            content += self._latexFormat( line, sections, tag )
        if tag.name == "ul":
            content += r"\end{itemize}" + "\n"
        if tag.name == "ol":
            content += r"\end{enumerate}" + "\n"
        elif tag.name == 'li':
            content += "\n"
        elif tag.name == 'i':
            content += r"}"
        elif tag.name == 'b':
            content += r"}"
        elif tag.name == 'tt':
            content += r"}"
        elif tag.name == 'pre':
            content += r"\end{Verbatim}" + "\n"
            content += r"\end{figure}" + "\n"
        elif tag.name == "dl":
            content += r"\end{description}" + "\n"
        elif tag.name == 'dt':
            content += r"]"
        elif tag.name == 'table':
            content += r"\end{longtable}" + "\n"
            content += r"\end{center}" + "\n"
            assert tableColumns > 0
            content = content.replace( "(TABLEDEF)", "|l" * tableColumns + "|" )
            if caption != "":
                content = content.replace( "(CAPTION)",
                                           r"\caption{" + caption + "}" )
            caption = ""
        elif tag.name == "tr":
            content += r"\\ \hline" + "\n"
            if tableHeader:
                tmp = content
                content += r"\endfirsthead" + "\n"
                content += r"\hline" + "\n"
                content += tmp;
                content += r"\endhead" + "\n"
            if tableColumns == 0:
                tableColumns = columns
            assert tableColumns == columns
            columns = 0
            tableHeader = False
        elif tag.name == "th":
            content += r"}"
        elif tag.name == "td":
            if len( tag.contents ) > 1:
                content += r"\vspace{3pt}" + "\n"
                content += r"\end{minipage}" + "\n"
        elif tag.name == "p":
            content += "\n"
        return content

    #---------------------------------------------------------------------------
    def _codeFormat( self, tag ):
        content = ""
        if isinstance( tag, NavigableString ):
            return self._latexString( tag, "listing" )
        for line in tag.contents:
            content += self._codeFormat( line )
        return content

    #---------------------------------------------------------------------------
    def _processContent( self, content ):
        global footnotes
        for i in xrange( 1, len( footnotes ) ):
            content = content.replace( "(FOOTNOTE%d)" % i, footnotes[i-1] )
        return content

#===============================================================================

snaffle = Snaffle( BASE + PAGE, DOC )
snaffle.retrieve()
snaffle.decode()
snaffle.output()
