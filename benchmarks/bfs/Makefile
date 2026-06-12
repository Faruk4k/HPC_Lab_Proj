CC   = g++
LD   = $(CC)
OBJDUMP = objdump

SVEOPT     =
SUFFIX_SVE =

ifneq ($(SVEOPT),)
  MARCH      = armv8-a+sve
  SUFFIX_SVE = -sve
else
  MARCH      = armv8-a
endif

CFLAGS  = -O2 -march=$(MARCH)
LDFLAGS =

ifneq ($(M5_PREFIX),)
  CFLAGS += -DUSEM5OPS -I$(M5_PREFIX)/include
  LDFLAGS += -L$(M5_PREFIX)/lib -lm5
  SUFFIX_M5  = -m5
endif

LDFLAGS += -static

SUFFIX = $(SUFFIX_SVE)$(SUFFIX_M5)

.PHONY: clean, veryclean


all: bfs$(SUFFIX).x bfs$(SUFFIX).dump

bfs$(SUFFIX).x: bfs.cpp
	$(CC) $(CFLAGS) $< $(LDFLAGS) -o $@

bfs$(SUFFIX).dump: bfs$(SUFFIX).x
	$(OBJDUMP) --disassemble $< > $@

clean:
	rm -f *.o *.x *.dump