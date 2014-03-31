/*
 copyright 2014, Chen Wei <weichen302@gmail.com>
 version 0.0.3
Implement astronomical algorithms for finding solar terms and moon phases.

Truncated VSOP87D for calculate Sun's apparent longitude;

Truncated LEA-406 for calculate Moon's apparent longitude;

Truncated IAU2000B from USNO NOVAS c source is used for nutation.

Reference:
    VSOP87: ftp://ftp.imcce.fr/pub/ephem/planets/vsop87
    LEA-406: S. M. Kudryavtsev (2007) "Long-term harmonic development of
             lunar ephemeris", Astronomy and Astrophysics 471, 1069-1075
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "astro.h"
#define MAXITER 20  /* max iteration for Secand Method */

/* solve the equation when function f(jd, angle) reaches zero by
 * Secand method
 */
double rootbysecand(double (*f)(double , double),
                    double angle, double x0, double x1, double precision)
{
    double fx0, fx1, x2;
    fx0 = (*f)(x0, angle);
    fx1 = (*f)(x1, angle);
    int i = 0;
    for (i = 0; i < MAXITER; i++) {
        if (fabs(fx1) < precision || fabs(x0 - x1) < precision)
            return x1;
        x2 = x1 - fx1 * (x1 - x0) / (fx1 - fx0);
        fx0 = fx1;
        fx1 = (*f)(x2, angle);
        x0 = x1;
        x1 = x2;
        //printf("debug in rootbysecand: iter = %d angle = %.9f \n", i, fx1);
    }
    printf("debug in rootbysecand: not found after %d iterations \n", i);
    return -1;
}

/* covernt radian to 0 - 2pi */
double normrad(double r) {
    r = fmod(r, TWOPI);
    if (r < 0)
        r += TWOPI;
    return r;
}

/* convert an angle in radians into (-pi, +pi} */
double npitopi(double r) {
    r = fmod(r, TWOPI);
    if (r > PI)
        r -= TWOPI;
    else if (r <= -1.0 * PI)
        r += TWOPI;
    return r;
}

/* Calculate the difference between target angle and solar geocentric
 * longitude at a given JDTT
 *
 * and normalize the angle between Sun's Longitude on a given
 * day and the angle we are looking for to (-pi, pi), therefore f(x) is
 * continuous from -pi to pi
 *
 */
double f_solarangle(double jd, double angle)
{
    return npitopi(apparentsun(jd, 0) - angle);
}

/* Calculate difference between target angle and current sun-moon angle
 *
 * Arg:
 *     jd: time in JDTT
 * Return:
 *     angle in radians, convert to -pi to +pi range
 *
 */
double f_msangle(double jd, double angle)
{
    return npitopi(apparentmoon(jd, 1) - apparentsun(jd, 1) - angle);
}

/* calculate Solar Term by secand method
 *
 * The Sun's moving speed on ecliptical longitude is 0.04 argsecond / second,
 *
 * The mean error of truncated VSOP is less than 0.1", nutation by IAU2000B is
 * 0.001"
 *
 * Args:
 *     year: the year in integer
 *     angle: degrees of the solar term
 * Return:
 *     time in JDTT
 *
 */
double solarterm(int year, double angle)
{
    /* mean error when compare apparentsun to NASA(1900-2100) is 0.05"
     * 0.000000005 radians = 0.001" */
    double ERROR, r, est_vejd, x0, x1;
    ERROR = 0.000000005;

    /* estimated date of Vernal Equinox, March 20.5 UTC0 */
    est_vejd = g2jd(year, 3, 20.5);

    /* negative angle means search backward from Vernal Equinox.
     * Initialize x0 to the day which apparent Sun longitude close to the
     * angle we searching for */

    x0 = est_vejd + angle * 360.0 / 365.24;
    x1 = x0 + 0.5;

    r = angle * DEG2RAD;
    return rootbysecand(f_solarangle, r, x0, x1, ERROR);
}

/* search newmoon near a given date.
 *
 * Angle between Sun-Moon has been converted to {-pi, pi} range so the
 * function f_msangle is continuous in that range. Use Secand method to find
 * root.
 *
 * Test shows newmoon can be found in 5 iterations, if the start is close
 * enough, it may use only 3 iterations.
 *
 * Arg:
 *     jd: in JDTT
 * Return:
 *     JDTT of newmoon
 *
 */
double newmoon(double jd)
{

    /* 0.0000001 radians is about 0.02 arcsecond, mean error of apparentmoon
     * when compared to JPL Horizon is about 0.7 arcsecond */
    double ERROR, x0, x1;
    ERROR = 0.0000001;

    /* initilize x0 to the day close to newmoon */
    x0 = jd - f_msangle(jd, 0) / MOON_SPEED;
    x1 = x0 + 0.5;
    return rootbysecand(f_msangle, 0, x0, x1, ERROR);
}

/* search new moon from specified start time
 *
 * Arg:
 *     start: the start time in JD, doesn't matter if it is in TT or UT
 *     count: the number of newmoons to search after start time
 *
 * Return:
 *     a list of JDTT when newmoon occure
 *
 */
void findnewmoons(double newmoons[], int nmcount, double startjd)
{
    int i;
    double nm;
    for ( i = 0; i < nmcount; i++) {
        nm = newmoon(startjd);
        newmoons[i] = nm;
        startjd = nm + SYNODIC_MONTH;
    }
}

/* convert decimal degree to d m s format string */
size_t fmtdeg(char *strdeg, double d) {
    if (abs(d) > 360)
        d = fmod(d, 360.0);
    double fdegree, deg, m, s, tmp;
    fdegree = fabs(d);

    tmp = modf(fdegree, &deg);
    tmp = modf(tmp * 60.0, &m);
    s = tmp * 60;

    char *sign = "";
    if (d < 0)
        sign = "-";
    sprintf(strdeg, "%s%d°%d%c%.6f%c", sign, (int)(deg),
                                          (int)(m), 39, s, 34);
    return strlen(strdeg);
}
