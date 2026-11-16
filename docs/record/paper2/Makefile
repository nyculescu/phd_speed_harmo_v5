# TinyTeX lives in the home directory and is not on the PATH (V458).
TEXBIN ?= $(HOME)/.TinyTeX/bin/x86_64-linux
export PATH := $(TEXBIN):$(PATH)

.PHONY: html pdf all clean
all:
	quarto render
html:
	quarto render --to html
pdf:
	quarto render --to pdf
clean:
	rm -rf _manuscript .quarto index_files
