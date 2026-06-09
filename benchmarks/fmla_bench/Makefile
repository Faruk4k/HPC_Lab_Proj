CC   = gcc
LD   = $(CC)
OBJDUMP = objdump

MARCH      = armv8-a+sve

CFLAGS  = -O2 -march=$(MARCH)
LDFLAGS =

ifneq ($(M5_PREFIX),)
  CFLAGS += -DUSEM5OPS -I$(M5_PREFIX)/include
  LDFLAGS += -L$(M5_PREFIX)/lib -lm5
  SUFFIX_M5  = -m5
endif

LDFLAGS += -static

SUFFIX = $(SUFFIX_M5)

.PHONY: clean, veryclean


all: fmla_bench$(SUFFIX).x fmla_bench$(SUFFIX).dump

fmla_bench$(SUFFIX).x: fmla_bench.c
	$(CC) $(CFLAGS) $< $(LDFLAGS) -o $@

fmla_bench$(SUFFIX).dump: fmla_bench$(SUFFIX).x
	$(OBJDUMP) --disassemble $< > $@

clean:
	rm -f *.o *.x *.dump
