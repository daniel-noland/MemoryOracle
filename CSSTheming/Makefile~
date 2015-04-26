
CC = lessc
CSS = "css"
LESS = "less"

SOURCES = $(shell ls less/*.less)
TARGETS = $(patsubst less/%.less,css/%.css,$(SOURCES))

css/%.css: less/%.less
	$(CC) $< > $@

all: $(TARGETS)
