#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "astro.h"

#define MAX_JPL_LINE_LEN 100
#define MAX_JPL_RECORDS  73415
#define FLAG_SOE 1

struct jplrcd {
    double jd;
    double lon;
};

int parsejplhorizon(char *fname, struct jplrcd *records[]);
struct jplrcd *lon_alloc(void);
void verify_apparent_sun_moon(void);
double n180to180(double angle);
double jd2year(double jd);

double jd2year(double jd)
{
    double fyear, jdyearstart;
    GregorianDate tmp;
    tmp = jd2g(jd);
    jdyearstart = g2jd(tmp.year, 1, 1.0);

    fyear = (double) tmp.year + (jd - jdyearstart) / 365.0;
    return fyear;
}

void testdeltat(void);
void testdeltat()
{
//    double d = -133.5;
//    int i;
    double jd;
    char strout[30];
    jd = jdptime("2012-01-05 18:00", "%y-%m-%d %H:%M", 0, 0);
    //jd = jdptime("2012-01-05", "%y-%m-%d", 0, 0);
    printf("%f\n", jd);
    jdftime(strout, jd, "%y-%m-%d %H:%M", 0, 0);
    printf("jdftime output = %s\n", strout);

    int i,year;
    double deltat;
    year = -500;
    for (i = 0; i < 20; i++) {
        deltat = deltaT(year, 1);
        printf("%d   = %.2f\n", year, deltat);
        year += 100;
    }
    return;
}

void testnewmoon_solarterm(void);
void testnewmoon_solarterm(void)
{
    double newmoons[NMCOUNT];
    double jd;
    //jd = jdptime("2014-01-01 18:00", "%y-%m-%d %H:%M", 0, 0);
    int year = 2000;
    int n;
    char isodt[30];
    int i;
    for (n = 0; n < 50; n++) {
        jd = g2jd(year, 1, 1.0);
        findnewmoons(newmoons, NMCOUNT, jd);
        year += 1;

        for (i = 0; i < NMCOUNT; i++) {
            jdftime(isodt, newmoons[i], "%y-%m-%d %H:%M:%S", 8.0, 1);
            printf("found newmoon: %s %.8f\n", isodt, newmoons[i]);
        }

    }

    double angle;
    for (angle = -90; angle < 285; angle += 15) {
        jd = solarterm(2014, angle);
        jdftime(isodt, jd, "%y-%m-%d %H:%M:%S", 8.0, 1);
        printf("solar term: %3.0f %s\n", angle, isodt);
    }
    return;
}

void testapparentmoon(void);
void testapparentmoon(void)
{
    double jd = 2411545.0;
    char deg[30];
    char degsun[30];
    double d;
    int i;
    for (i = 0; i < 20; i++) {
        d = apparentmoon(jd, 1) * RAD2DEG;
        fmtdeg(deg, d);
        d = lightabbr_high(jd) * RAD2DEG;

        fmtdeg(degsun, d);
        printf("%.2f %s %s\n", jd, deg, degsun);
        jd += 2;
    }
}

void testnutation(void);
void testnutation(void)
{
    double jd = 2411545.0;
    char deg[30];
    double d;
    d = nutation(jd) * RAD2DEG;
    fmtdeg(deg, d);
    printf("%s\n", deg);
}


static char buf[MAX_JPL_LINE_LEN];

int parsejplhorizon(char *fname, struct jplrcd *records[])
{
    FILE *fp;
    char *p;
    int i, flag;
    struct jplrcd *plon;
    if ((fp = fopen(fname, "r")) == NULL) {
        printf("can not open %s\n", fname);
        exit(2);
    }
    flag = 0;
    i = 0;
    while ((p = fgets(buf, MAX_JPL_LINE_LEN + 1, fp)) != NULL
                                                 && i < MAX_JPL_RECORDS) {
        if (p == strstr(p, "$$SOE")) {  /* start of records */
            flag = 1;
            continue;
        } else if (p == strstr(p, "$$EOE")) {
            break;
        }

        if (flag) {
            plon = lon_alloc();
            sscanf(p, "%lf %lf", &(plon->jd), &(plon->lon));
            records[i++] = plon;
        }

    }
    return i;
}


struct jplrcd *lon_alloc(void)
{
    return (struct jplrcd *) malloc(sizeof(struct jplrcd));
}


/* verify accuracy against JPL
 * output can be save and used for gnuplot
 */
void verify_apparent_sun_moon(void)
{
    int lensun, lenmoon;
    int i, step, count;
    double delta_sun, delta_moon;
    double delta_sun_n, delta_sun_p, delta_moon_n, delta_moon_p;
    struct jplrcd *jplsun[MAX_JPL_RECORDS];
    struct jplrcd *jplmoon[MAX_JPL_RECORDS];

    lensun  = parsejplhorizon("jpl_sun.txt",  jplsun);
    lenmoon = parsejplhorizon("jpl_moon.txt", jplmoon);
    step = 1;
    i = 0;
    count = 0;
    delta_sun_n = 0;
    delta_sun_p = 0;
    delta_moon_n = 0;
    delta_moon_p = 0;
    while (i < lensun) {
        if (jplsun[i]->jd == jplmoon[i]->jd) {
            delta_sun = n180to180(apparentsun(jplsun[i]->jd, 0) * RAD2DEG
                                    - jplsun[i]->lon) * 3600;
            delta_moon = n180to180(apparentmoon(jplmoon[i]->jd, 0) * RAD2DEG
                                 - jplmoon[i]->lon) * 3600;
            if (delta_sun > 0)
                delta_sun_p += delta_sun;
            else
                delta_sun_n += delta_sun;

            if (delta_moon > 0)
                delta_moon_p += delta_moon;
            else
                delta_moon_n += delta_moon;
            count++;

            printf("%.2f  %.9f  %.9f\n",
                    jd2year(jplsun[i]->jd), delta_moon, delta_sun);
        }
        i += step;
    }

    printf("\n# total records of JPL Sun = %d Moon=%d\n", lensun, lenmoon);
    printf("# Mean Error (arcsec):\n");
    printf("# Sun: +%.4f / %.4f   Moon: +%.4f / %.4f\n",
                                delta_sun_p / count, delta_sun_n / count,
                                delta_moon_p / count, delta_moon_n / count);
}

double n180to180(double angle)
{
    angle = fmod(angle, 360.0);
    if (angle > 180.0)
        angle += -360.0;
    else if (angle <= -180.0)
        angle += 360;
    return angle;
}

int main(void);
int main()
{
    //testnewmoon_solarterm();
    //testapparentmoon();
    //testnutation();
    verify_apparent_sun_moon();
    return 0;
}
