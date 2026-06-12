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


all: merge$(SUFFIX).x merge-omp$(SUFFIX).x merge$(SUFFIX).dump

merge-omp$(SUFFIX).dump: merge-omp$(SUFFIX).x
	$(OBJDUMP) --disassemble -mattr=+sve $< > $@

merge-omp$(SUFFIX).x: merge.c
	$(CC) $(CFLAGS) $< $(LDFLAGS) -fopenmp -o $@
#	$(CC) $(CFLAGS) $(LDFLAGS) -fopenmp $< $(LIBS) -o $@

merge$(SUFFIX).x: merge.c
	$(CC) $(CFLAGS) $< $(LDFLAGS) -o $@

merge$(SUFFIX).dump: merge$(SUFFIX).x
	$(OBJDUMP) --disassemble $< > $@


clean:
	rm -f *.o *.x *.dump
