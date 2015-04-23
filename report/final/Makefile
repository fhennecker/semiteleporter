.PHONY: all clean mrproper

all: report.pdf

clean:
	rm -f *.log *.aux *.toc *.out *.lof

mrproper: clean
	rm -f report.pdf

%.pdf: %.tex
	pdflatex $<
	#Second time for ToC etc...
	pdflatex $<
