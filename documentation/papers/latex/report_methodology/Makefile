SHELL := /bin/bash
filename=report

text: html
	html2text -width 100 -style pretty ${filename}/${filename}.html | sed -n '/./,$$p' | head -n-2 >${filename}.txt

html:
	@#latex2html -split +0 -info "" -no_navigation ${filename}
	htlatex ${filename}

pdf: ${filename}.tex
	pdflatex ${filename}
	bibtex ${filename}||true
	pdflatex ${filename}
	pdflatex ${filename}

read:
	evince ${filename}.pdf &

aread:
	acroread ${filename}.pdf

clean:
	rm -f ${filename}.{4ct,4tc,aux,bbl,blg,css,dvi,html,idv,lg,lof,log,lot,out,pdf,ps,run.xml,tmp,toc,txt,xref}
	rm -f ${filename}*x.png
	rm -f *blx.bib
