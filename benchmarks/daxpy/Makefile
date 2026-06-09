CC   = gcc
LD   = $(CC)
OBJDUMP = objdump

SVEOPT     = 
SUFFIX_SVE =

ifneq ($(SVEOPT),)
  MARCH      = armv8-a+sve
  SUFFIX_SVE = -sve
else
  #MARCH      = armv8-a+simd
  MARCH      = armv8-a -fno-tree-vectorize
endif

CFLAGS  = -O3 -march=$(MARCH)
LDFLAGS =

ifneq ($(M5_PREFIX),)
  CFLAGS += -DUSEM5OPS -I$(M5_PREFIX)/include
  LDFLAGS += -L$(M5_PREFIX)/lib -lm5
  SUFFIX_M5  = -m5
endif

ifneq ($(ARMIE_USED),)
  CFLAGS += -DUSEARMIE
endif

LDFLAGS += -static

SUFFIX = $(SUFFIX_SVE)$(SUFFIX_M5)

.PHONY: clean, veryclean


all: daxpy$(SUFFIX).x daxpy$(SUFFIX).s \
     daxpy$(SUFFIX).dump \
     

daxpy$(SUFFIX).x: daxpy.c
	$(CC) $(CFLAGS) $< $(LDFLAGS) -o $@

daxpy$(SUFFIX).s: daxpy.c
	$(CC) $(CFLAGS) -S $< $(LDFLAGS) -o $@

daxpy$(SUFFIX).dump: daxpy$(SUFFIX).x
	$(OBJDUMP) --disassemble $< > $@

clean:
	rm -f *.o *.x *.s *.dump
