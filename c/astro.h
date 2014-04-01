/*
 * header for astro functions
 */

#include <stdio.h>
#define PI        3.14159265358979323846
#define TWOPI     6.28318530717958647693
#define RAD2DEG  57.295779513082320876798
#define DEG2RAD   0.017453292519943295779
#define ASEC2RAD  4.848136811095359935899141e-6
#define ASEC360        1296000.0
#define J2000          2451545.0
#define TROPICAL_YEAR     365.24
#define SYNODIC_MONTH      29.53
#define MOON_SPEED  TWOPI / SYNODIC_MONTH  /* approximate Moon & Sun's */
#define SUN_SPEED   TWOPI / TROPICAL_YEAR  /* longitude change per day*/
#define NMCOUNT  15    /* default search total 15 new moons */
#define ISODTLEN 30    /* max length of ISO date string */
#define MAX_THREADS 32  /* max number of threads for compute lea406-full */
#define MAX_CPUINFO_LEN 1000  /* max line buf size when parse /proc/cpuinfo */

typedef struct {
    int year;
    int month;
    double day;
} GregorianDate;

struct worker_param {
    int tid;
    double tc;           /* t in century */
};

/* Function prototypes */

GregorianDate jd2g(double jd);
size_t fmtdeg(char *strdeg, double d);

double normrad(double r);

double npitopi(double r);

double jdptime(char *isodt, char *fmt, double tz, int isut);

size_t jdftime(char *isodt, double jd, char *fmt, double tz, int isut);

double g2jd(int year, int month, double day);

double deltaT(int year, int month);

double apparentsun(double jd, int ignorenutation);

double apparentmoon(double jd, int ignorenutation);

double lea406(double jd, int ignorenutation);

void *lea406worker(void *args);

double nutation(double jd);

double lightabbr_high(double jd);

double vsopLx(double vsopterms[][3], size_t rowcount, double t);

double vsop(double jd);

double rootbysecand(double (*f)(double , double),
                    double angle, double x0, double x1, double precision);

double f_solarangle(double jd, double angle);

double f_msangle(double jd, double angle);

double newmoon(double jd);

void findnewmoons(double newmoons[], int nmcount, double startjd);

double solarterm(int year, double angle);

int findastro(int year);

int cpucount(void);
