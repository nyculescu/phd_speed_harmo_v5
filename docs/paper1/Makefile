# TinyTeX lives in the home directory and is not on the PATH (V458).
TEXBIN ?= $(HOME)/.TinyTeX/bin/x86_64-linux
export PATH := $(TEXBIN):$(PATH)

.PHONY: pdf clean
pdf:
	latexmk main.tex
clean:
	latexmk -C main.tex
