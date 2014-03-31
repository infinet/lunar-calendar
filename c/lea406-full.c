/*
 copyright 2014, Chen Wei <weichen302@gmail.com>
 version 0.0.3
Implement astronomical algorithms for finding solar terms and moon phases.

Truncated LEA-406 for calculate Moon's apparent longitude;

Reference:
    LEA-406: S. M. Kudryavtsev (2007) "Long-term harmonic development of
             lunar ephemeris", Astronomy and Astrophysics 471, 1069-1075
*/

#include <stdio.h>
#include <math.h>
#include "astro.h"
#include "lea406-full.h"

/*
 * LEA-406 Moon Solution
 *
 * Reference:
 *     Long-term harmonic development of lunar ephemeris.
 *         Kudryavtsev S.M.  <Astron. Astrophys. 471, 1069 (2007)>
 *
 */

/* compute moon ecliptic longitude using lea406 */
double lea406(double jd, int ignorenutation) {
    double t, tm, tm2;
    t = (jd - J2000) / 36525.0;
    tm = t / 10.0;
    tm2 = tm * tm;

    double V, arg;
    V = FRM[0] + (((FRM[4] * t + FRM[3]) * t + FRM[2]) * t + FRM[1]) * t;

    int i;
    for (i = 0; i < LEA406TERMS; i++) {
        arg = (M_ARG[i][0] + t * (M_ARG[i][1] + M_ARG[i][2] * t)) * ASEC2RAD;
        V +=    M_AP[i][0] * sin(arg + M_AP[i][3] * DEG2RAD)
              + M_AP[i][1] * sin(arg + M_AP[i][4] * DEG2RAD) * tm
              + M_AP[i][2] * sin(arg + M_AP[i][5] * DEG2RAD) * tm2;
    }

    V *= ASEC2RAD;

    if (!ignorenutation) {
        V += nutation(jd);
        /* printf("debug lea406,  nutation been adjusted"); */
    }
    return V;
}

/* calculate the apparent position of the Moon, it is an alias to the
 * lea406 function
 */
double apparentmoon(double jd, int ignorenutation)
{
    return lea406(jd, ignorenutation);
}
