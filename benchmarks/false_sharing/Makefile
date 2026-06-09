CC      = gcc
LD      = $(CC)
OBJDUMP = objdump

SVEOPT  = 

ifneq ($(SVEOPT),)
  MARCH      = armv8-a+sve
  SUFFIX_SVE = -sve
else
  # No vectorization compilation
  MARCH      = armv8-a -fno-tree-vectorize
endif

CFLAGS  = -O3 -march=$(MARCH)
LDFLAGS = 

ifneq ($(M5_PREFIX),)
  CFLAGS += -DUSEM5OPS -I$(M5_PREFIX)/include
  LDFLAGS += -L$(M5_PREFIX)/lib -lm5
  SUFFIX_M5  = -m5
endif

LDFLAGS += -static -lpthread

SUFFIX = $(SUFFIX_SVE)$(SUFFIX_M5)

.PHONY: clean, veryclean

all: false_sharing_nopad$(SUFFIX).x

### cache line padding implemented (avoid false sharing)
#false_sharing_pad$(SUFFIX).x: false_sharing.c
#	$(CC) $(CFLAGS) $< -DPADDING_USED $(LDFLAGS) -o $@

### no cache line padding implemented
false_sharing_nopad$(SUFFIX).x: false_sharing.c
	$(CC) $(CFLAGS) $< $(LDFLAGS) -o $@


clean:
	rm -f *.o *.x *.dump
