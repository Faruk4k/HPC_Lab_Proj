CC   = gcc
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

CFLAGS  = -O3 -march=$(MARCH)
LDFLAGS =

ifneq ($(M5_PREFIX),)
  CFLAGS += -DUSEM5OPS -I$(M5_PREFIX)/include
  LDFLAGS += -L$(M5_PREFIX)/lib -lm5
  SUFFIX_M5  = -m5
endif

LDFLAGS += -static

SUFFIX = $(SUFFIX_SVE)$(SUFFIX_M5)

.PHONY: clean, veryclean


all: simple_triad$(SUFFIX).x simple_triad-omp$(SUFFIX).x simple_triad$(SUFFIX).dump

simple_triad-omp$(SUFFIX).dump: simple_triad-omp$(SUFFIX).x
	$(OBJDUMP) --disassemble -mattr=+sve $< > $@

simple_triad-omp$(SUFFIX).x: simple_triad.c
	$(CC) $(CFLAGS) $< $(LDFLAGS) -fopenmp -o $@
#	$(CC) $(CFLAGS) $(LDFLAGS) -fopenmp $< $(LIBS) -o $@

simple_triad$(SUFFIX).x: simple_triad.c
	$(CC) $(CFLAGS) $< $(LDFLAGS) -o $@

simple_triad$(SUFFIX).dump: simple_triad$(SUFFIX).x
	$(OBJDUMP) --disassemble $< > $@


clean:
	rm -f *.o *.x *.dump
