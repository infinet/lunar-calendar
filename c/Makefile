CC = gcc
CFLAGS = -Wall -O2
LIBS = -lm
SRCS = lunarcal.c lunarcalbase.c lunarcalbase.h \
	astro.c astro.h vsop.c nutation.c julian.c \
	lea406-full.c lea406-full.h 
OBJS = $(SRCS:.c=.o)
TESTSRCS = testastro.c \
	astro.c astro.h vsop.c nutation.c julian.c \
	lea406-full.c lea406-full.h 
TESTOBJS = $(TESTSRCS:.c=.o)
LUNARCAL = lunarcal
TESTASTRO = testastro
EXECUTABLE = lunarcal

all: $(LUNARCAL) $(TESTASTRO)
	@echo all compiled

$(LUNARCAL): $(OBJS) 
	$(CC) $(CFLAGS) -o $(LUNARCAL) $(OBJS) $(LIBS)

$(TESTASTRO): $(TESTOBJS) 
	$(CC) $(CFLAGS) -o $(TESTASTRO) $(TESTOBJS) $(LIBS)

.c.o:
	$(CC) $(CFLAGS) -c $< -o $@
	    
clean:
	rm -f *.o core a.out astro lunarcal testastro

