# Static recompilation of Simon the Sorcerer: the translated program and music
# module (gen/<name>/, from SuperSpider's analyse and gen via
# ../tools/images.py) and game.c, linked with libroger (the RISC OS runtime).
ROGER   ?= $(HOME)/stuff/libroger
SS      ?= $(HOME)/stuff/superspider
CC      ?= gcc
CFLAGS  ?= -O2 -g -w -fno-strict-aliasing $(if $(TRACE),-DRECOMP_TRACE)
GEN     := $(wildcard gen/*/code*.c) $(wildcard gen/*/entries.c)
OBJ     := $(GEN:.c=.o) game.o
LIBS    := $(shell pkg-config --libs sdl3) -ljpeg -lm -lpthread
INC     := -I$(ROGER)/include

simon: $(OBJ) $(ROGER)/libroger.a
	$(CC) $(CFLAGS) -o $@ $(OBJ) $(ROGER)/libroger.a $(LIBS)

$(ROGER)/libroger.a: FORCE
	$(MAKE) -C $(ROGER) libroger.a

gen/%.o: gen/%.c $(ROGER)/include/roger_cpu.h
	$(CC) $(CFLAGS) $(INC) -c -o $@ $<

game.o: game.c gen/modules.inc $(ROGER)/include/roger.h
	$(CC) $(CFLAGS) $(INC) -c -o $@ $<

# make regen: analyse and translate every image
regen:
	rm -rf gen
	SUPERSPIDER=$(SS) python3 ../tools/images.py analyse gen

LOG ?= untranslated.log
roots:
	SUPERSPIDER=$(SS) python3 ../tools/images.py roots $(LOG)

clean:
	rm -f gen/*/*.o game.o simon

.PHONY: FORCE regen roots clean
