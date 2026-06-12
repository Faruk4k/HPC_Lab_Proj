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


all: quick$(SUFFIX).x quick-omp$(SUFFIX).x quick$(SUFFIX).dump

quick-omp$(SUFFIX).dump: quick-omp$(SUFFIX).x
	$(OBJDUMP) --disassemble -mattr=+sve $< > $@

quick-omp$(SUFFIX).x: quick.c
	$(CC) $(CFLAGS) $< $(LDFLAGS) -fopenmp -o $@
#	$(CC) $(CFLAGS) $(LDFLAGS) -fopenmp $< $(LIBS) -o $@

quick$(SUFFIX).x: quick.c
	$(CC) $(CFLAGS) $< $(LDFLAGS) -o $@

quick$(SUFFIX).dump: quick$(SUFFIX).x
	$(OBJDUMP) --disassemble $< > $@


clean:
	rm -f *.o *.x *.dump
