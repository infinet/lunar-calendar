
CC = gcc
CFLAGS = -Wall -O2
LIBS = -lm -lpthread

LUNARCAL = lunarcal
TESTASTRO = testastro

# default target
.PHONY : all
all: $(LUNARCAL) $(TESTASTRO)
	@echo all done!

OBJS =
OBJS += astro.o
OBJS += vsop.o
OBJS += nutation.o
OBJS += julian.o
OBJS += lea406-full.o

LUNARCAL_OBJS = $(OBJS)
LUNARCAL_OBJS += lunarcalbase.o
LUNARCAL_OBJS += lunarcal.o

TESTASTRO_OBJS = $(OBJS)
TESTASTRO_OBJS += testastro.o

$(LUNARCAL_OBJS) $(TESTASTRO_OBJS): astro.h
lunarcalbase.o lunarcal.o: lunarcalbase.h
lea406-full.o:  lea406-full.h

$(LUNARCAL): $(LUNARCAL_OBJS)
	$(CC) $(CFLAGS) -o $(LUNARCAL) $(LUNARCAL_OBJS) $(LIBS)

$(TESTASTRO): $(TESTASTRO_OBJS)
	$(CC) $(CFLAGS) -o $(TESTASTRO) $(TESTASTRO_OBJS) $(LIBS)


.PHONY : clean
clean:
	rm -f *.o core a.out astro lunarcal testastro
