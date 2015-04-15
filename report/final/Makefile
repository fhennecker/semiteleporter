all: report.pdf

%.pdf: %.tex
	pdflatex $<
	#Second time for ToC etc...
	pdflatex $<