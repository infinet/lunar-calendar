/*
 * functions convert between Gregorian date and Julian date
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "astro.h"

/* convert a Gregorian date to JD from AA, p61 */
double g2jd(int year, int month, double day)
{
    if (month <= 2) {
        year -= 1;
        month += 12;
    }

    int a, b, isjulian;
    double jd;

    a = (int) (year / 100);
    isjulian = 0;
    if (year < 1582) {
        isjulian = 1;
    } else if (year == 1582) {
        if (month  < 10)
            isjulian = 1;

        if (month == 10 && day <= 5.0)
            isjulian = 1;

        if (month == 10 && day > 5.0 && day < 15.0)
            return 2299160.5;
    }

    if (isjulian)
        b = 0;
    else
        b = 2 - a + (int) (a / 4);

    /* 30.6001 is a hack Meeus suggested */
    jd =  (int) (365.25 * (year + 4716)) + (int) (30.6001 * (month + 1))
          + day + b - 1524.5;
    return jd;
}

/*  convert JD to Gregorian date */
GregorianDate jd2g(double jd)
{
    jd += 0.5;
    int a, b, c, d, e, z, alpha;
    double f;
    GregorianDate res;

    z = (int) (jd);
    f = fmod(jd, 1.0);  // decimal part
    if (z < 2299161) {
        a = z;
    } else {
        alpha = (int) ((z - 1867216.25) / 36524.25);
        a = z + 1 + alpha - (alpha / 4);
    }
    b = a + 1524;
    c = (int) ((b - 122.1) / 365.25);
    d = (int) (365.25 * c);
    e = (int) ((b - d) / 30.6001);
    res.day = (float) (b - d - (int) (30.6001 * e) + f);
    if (e < 14)
        res.month = e - 1;
    else
        res.month = e - 13;

    if (res.month > 2)
        res.year = c - 4716;
    else
        res.year = c - 4715;

    return res;
}

/* Args:
 *     isodt: datetime string in ISO format
 *     tz: a integer as timezone, e.g. -8 for UTC-8, 2 for UTC2
 *     fmt: like strftime but currently only support three format
 *          %y-%m-%d %H:%M:%S
 *          %y-%m-%d %H:%M
 *          %y-%m-%d
 *     ut: convert to UTC(adjust delta T)
 * Return:
 *     Julian Day
 *
 */
double jdptime(char *isodt, char *fmt, double tz, int isut)
{
    char inputstr[40];
    char *isodate;
    char *isot;

    strcpy(inputstr, isodt);

    if (strcmp(fmt, "%y-%m-%d") == 0) {
        char isodatestr[40];
        char isotstr[40];
        isodate = strcpy(isodatestr, isodt);
        isot    = strcpy(isotstr, "00:00:00");
    } else if (strcmp(fmt, "%y-%m-%d %H:%M") == 0) {
        isodate = strtok(inputstr, " ");
        isot    = strtok(NULL, " ");
    } else {
        isodate = strtok(inputstr, " ");
        isot    = strtok(NULL, " ");
    }

    char *sy;
    char *sm, *sd, *shour, *sminute, *ssec;
    double d, hour, minute, sec;
    GregorianDate g;

    sy = strtok(isodate, "-");
    sm = strtok(NULL, "-");
    sd = strtok(NULL, "-");
    g.year  = atoi(sy);
    g.month = atoi(sm);

    d = atof(sd);

    shour   = strtok(isot, ":");
    sminute = strtok(NULL, ":");
    ssec    = strtok(NULL, ":");
    hour   = atof(shour);
    minute = atof(sminute);
    if (ssec)
        sec = atof(ssec);
    else
        sec = 0;

    d += (hour * 3600.0 + minute * 60.0 + sec) / 86400.0;
    g.day = d;

    return g2jd(g.year, g.month, g.day);
}

/*  format a Julian Day to ISO format datetime

    Args:
        jd: time in JDTT
        tz: a integer as timezone, e.g. -8 for UTC-8, 2 for UTC2
        fmt: like strftime but currently only support three format
             %y-%m-%d %H:%M:%S
             %y-%m-%d %H:%M
             %y-%m-%d
        ut: convert to UTC(adjust delta T)

    Return:
        time string in ISO format, e.g. 1984-01-01 23:59:59
*/
size_t jdftime(char *isodt, double jd, char *fmt, double tz, int isut)
{

    GregorianDate g;
    double deltat, utsec, secs, jdut;
    int isecs;
    /* char isodt[ISODTLEN]; */
    g = jd2g(jd);

    deltat = isut ? deltaT(g.year, g.month) : 0;

    /* convert jd to seconds, then adjust deltat */
    utsec = jd * 86400.0 + tz * 3600.0 - deltat;

    jdut = utsec / 86400.0;

    /* get time in seconds directly to minimize round error */
    secs = fmod(utsec + 43200.0, 86400.0);

    if (strcmp(fmt, "%y-%m-%d %H:%M") == 0) {
        isecs = (int)(floor(0.5 + secs / 60.0) * 60.0);
    } else {
        isecs = (int)(secs);
    }
    if (86400 == secs) {
        jdut = floor(jdut) + 0.5;
        isecs = 0;
    }

    g = jd2g(jdut);

    /* use integer math hereafter */
    int y, m, d, H, M, S, ms;
    y = g.year;
    m = g.month;
    d = floor(g.day);
    H = isecs / 3600;
    ms = isecs % 3600;
    M = ms / 60;
    S = ms % 60;

    if (strcmp(fmt, "%y%m%d") == 0) {
        sprintf(isodt, "%04d%02d%02d", y, m, d);
    } else if (strcmp(fmt, "%y-%m-%d") == 0) {
        sprintf(isodt, "%04d-%02d-%02d", y, m, d);
    } else if (strcmp(fmt, "%y-%m-%d %H:%M") == 0) {
        sprintf(isodt, "%04d-%02d-%02d %02d:%02d", y, m, d, H, M);
    } else {
        sprintf(isodt, "%04d-%02d-%02d %02d:%02d:%02d", y, m, d, H, M, S);
    }

    return strlen(isodt);
}

/*
     Polynomial Expressions for Delta T (ΔT) from nasa. Valid for -1999 to
    +3000.  http://eclipse.gsfc.nasa.gov/LEcat5/deltatpoly.html

    Arg:
        year: Gregorian year in integer
        m:    Gregorian month in integer
        d:    doesn't matter
    Result:
        ΔT in seconds

    verfify against historical records from NASA

     year  history   computed  diff
     -500    17190   17195.37   5.4
     -400    15530   15523.84   6.2
     -300    14080   14071.97   8.0
     -200    12790   12786.59   3.4
     -100    11640   11632.52   7.5
        0    10580   10578.95   1.0
      100     9600    9592.45   7.6
      200     8640    8636.34   3.7
      300     7680    7676.67   3.3
      400     6700    6694.67   5.3
      500     5710    5705.50   4.5
      600     4740    4734.89   5.1
      700     3810    3809.04   1.0
      800     2960    2951.97   8.0
      900     2200    2197.11   2.9
     1000     1570    1571.65   1.7
     1100     1090    1086.99   3.0
     1200      740     735.10   4.9
     1300      490     490.98   1.0
     1400      320     321.09   1.1
     1500      200     197.85   2.2
     1600      120     119.55   0.5
     1700        9       8.90   0.1
     1750       13      13.44   0.4
     1800       14      13.57   0.4
     1850        7       7.16   0.2
     1900       -3      -2.12   0.9
     1950       29      29.26   0.3
     1955       31      31.23   0.1
     1960       33      33.31   0.1
     1965       36      36.13   0.4
     1970       40      40.66   0.5
     1975       46      45.94   0.4
     1980       50      50.93   0.4
     1985       54      54.60   0.3
     1990       57      57.20   0.3
     1995       61      61.17   0.4
     2000       64      64.00   0.2
     2005       65      64.85   0.1

     Also, JPL uses "last known leap-second is used over any future interval".
     It causes the large error when compare apparent sun/moon position with JPL
     Horizon

 */
double deltaT(int year, int month) {
    double y, m,  u;
    m = (double) month;
    y = year + (m - 0.5) / 12.0;
    if (year < -500) {
        u = (year - 1820) / 100.0;
        return -20 + 32 * u * u;
    } else if (year < 500) {
        u = y / 100.0;
        return  10583.6 + u * (-1014.41 +
                          u * (33.78311 +
                          u * (-5.952053 +
                          u * (-0.1798452 +
                          u * (0.022174192 +
                          u * 0.0090316521)))));
    } else if (year < 1600) {
        u = (y -1000) / 100.0;
        return  1574.2 + u * (-556.01 +
                         u * (71.23472 +
                         u * (0.319781 +
                         u * (-0.8503463 +
                         u * (-0.005050998 +
                         u * 0.0083572073)))));
    } else if (year < 1700) {
        u = y -1600;
        return 120 + u * (-0.9808 +
                     u * (- 0.01532 +
                     u / 7129));
    } else if (year < 1800) {
        u = y - 1700;
        return 8.83 + u * (0.1603 +
                        u * (-0.0059285 +
                        u * (0.00013336 +
                        u / -1174000)));
    } else if (year < 1860) {
        u = y - 1800;
        return 13.72 + u * (-0.332447 +
                        u * (0.0068612 +
                        u * (0.0041116 +
                        u * (-0.00037436 +
                        u * (0.0000121272 +
                        u * (-0.0000001699 +
                        u * 0.000000000875))))));
    } else if (year < 1900) {
        u = y - 1860;
        return 7.62 + u * (0.5737 +
                        u * (-0.251754 +
                        u * (0.01680668 +
                        u * (-0.0004473624 +
                        u / 233174))));
    } else if (year < 1920) {
        u = y - 1900;
        return -2.79 + u * (1.494119 +
                        u * (-0.0598939 +
                        u * (0.0061966 +
                        u * -0.000197)));
    } else if (year < 1941) {
        u = y - 1920;
        return 21.20 + u * (0.84493 +
                        u * (-0.076100 +
                        u * 0.0020936));
    } else if (year < 1961) {
        u = y - 1950;
        return 29.07 + u * (0.407 +
                        u * (-1.0 / 233 +
                        u / 2547));
    } else if (year < 1986) {
        u = y - 1975;
        return  45.45 + u * (1.067 +
                        u * (-1.0 / 260 +
                        u / -718));
    } else if (year < 2005) {
        u = y -2000;
        return 63.86 + u * (0.3345 +
                        u * (-0.060374 +
                        u * (0.0017275 +
                        u * (0.000651814 +
                        u * 0.00002373599))));
/*
 *     else:
 *         JPL uses "last known leap-second is used over any future interval" .
 *         It causes the large error when compare apparent sun/moon position
 *         with JPL Horizon
 *
 *         return 67.182963
 *
 */
    } else if (year < 2050) {
        u = y -2000;
        return 62.92 + u * (0.32217 + u * 0.005589);
    } else if (year < 2150) {
        u = (y - 1820.0) / 100.0;
        return -20 + 32 * u * u - 0.5628 * (2150 - y);
    } else {
        u = (y - 1820.0) / 100.0;
        return -20 + 32 * u * u;
    }
}
