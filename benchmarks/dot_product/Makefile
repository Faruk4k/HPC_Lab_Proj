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

all: dot_product_v1$(SUFFIX).x dot_product_v2$(SUFFIX).x 

dot_product_v1$(SUFFIX).x: dot_product.c
	$(CC) $(CFLAGS) $< -DPARA_V1_USED $(LDFLAGS) -o $@

dot_product_v2$(SUFFIX).x: dot_product.c
	$(CC) $(CFLAGS) $< -DPARA_V2_USED $(LDFLAGS) -o $@

dot_product_v3$(SUFFIX).x: dot_product.c
	$(CC) $(CFLAGS) $< -DPARA_V3_USED $(LDFLAGS) -o $@

clean:
	rm -f *.o *.x *.dump
