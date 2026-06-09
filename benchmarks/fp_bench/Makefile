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

CFLAGS  = -O0 -march=$(MARCH)
LDFLAGS =

ifneq ($(M5_PREFIX),)
  CFLAGS += -DUSEM5OPS -I$(M5_PREFIX)/include
  LDFLAGS += -L$(M5_PREFIX)/lib -lm5
  SUFFIX_M5  = -m5
endif

LDFLAGS += -static

SUFFIX = $(SUFFIX_SVE)$(SUFFIX_M5)

.PHONY: clean, veryclean


all: fp_bench$(SUFFIX).x fp_bench$(SUFFIX).dump

fp_bench$(SUFFIX).x: fp_bench.c
	$(CC) $(CFLAGS) $< $(LDFLAGS) -o $@

fp_bench$(SUFFIX).dump: fp_bench$(SUFFIX).x
	$(OBJDUMP) --disassemble $< > $@

clean:
	rm -f *.o *.x *.dump
