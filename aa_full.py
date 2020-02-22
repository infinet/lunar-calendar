#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' Implement astronomical algorithms for finding solar terms and moon phases.

Full VSOP87D for calculate Sun's apparent longitude;

Full LEA-406 for calculate Moon's apparent longitude;

Truncated IAU2000B from USNO NOVAS c source is used for nutation.

Reference:
    VSOP87: ftp://ftp.imcce.fr/pub/ephem/planets/vsop87
    LEA-406: S. M. Kudryavtsev (2007) "Long-term harmonic development of
             lunar ephemeris", Astronomy and Astrophysics 471, 1069-1075

'''

__license__ = 'BSD'
__copyright__ = '2020, Chen Wei <weichen302@gmail.com>'
__version__ = '0.0.3'

import math
from math import pi, fmod

import numpy as np
import numexpr as ne
from aa import lightabbr_high
from aa import nutation
from aa import fmtdeg
from aa import g2jd, jd2g

J2000 = 2451545.0
SYNODIC_MONTH = 29.53
MOON_SPEED = 2 * pi / SYNODIC_MONTH
TROPICAL_YEAR = 365.24
ASEC2RAD = 4.848136811095359935899141e-6
DEG2RAD = 0.017453292519943295
ASEC360 = 1296000.0
PI = pi
TWOPI = 2 * pi


def vsopLx(vsopterms, t):
    ''' helper function for calculate VSOP87 '''

    lx = vsopterms[:, 0] * np.cos(vsopterms[:, 1] + vsopterms[:, 2] * t)

    return sum(lx)

# full VSOP87D tables
from aa_full_table import EAR_L0, EAR_L1, EAR_L2, EAR_L3, EAR_L4, EAR_L5


def vsop(jde, FK5=True):
    ''' Calculate ecliptical longitude of earth in heliocentric coordinates,
    use VSOP87D table, heliocentric spherical, coordinates referred to the mean
    equinox of the date,

    In A&A, Meeus said while the complete VSOP87 yields an accuracy of 0.01",
    the abridge VSOP87 has an accuracy  of 1" for -2000 - +6000.

    The VSOP87D table used here is a truncated version, done by the
    vsoptrunc-sph.c from Celestia.

    Arg:
        jde: in JDTT
    Return:
        earth longitude in radians, referred to mean dynamical ecliptic and
        equinox of the date

        '''

    t = (jde - J2000) / 365250.0
    L0 = vsopLx(EAR_L0, t)
    L1 = vsopLx(EAR_L1, t)
    L2 = vsopLx(EAR_L2, t)
    L3 = vsopLx(EAR_L3, t)
    L4 = vsopLx(EAR_L4, t)
    L5 = vsopLx(EAR_L5, t)

    lon = (L0 + t * (L1 + t * (L2 + t * (L3 + t * (L4 + t * L5)))))

    if FK5:
        #b0 = vsopLx(earth_B0, t)
        #b1 = vsopLx(earth_B1, t)
        #b2 = vsopLx(earth_B2, t)
        #b3 = vsopLx(earth_B3, t)
        #b4 = vsopLx(earth_B4, t)
        #lat = b0 + t * (b1 + t * (b2 + t * (b3 + t * b4 )))
        #lp = lon - 1.397 * t - 0.00031 * t * t
        #deltalon = (-0.09033 + 0.03916 * (cos(lp) + sin(lp))
        #                             * tan(lat)) * ASEC2RAD
        #print 'FK5 convertion: %s' % fmtdeg(math.degrees(deltalon))
        # appears -0.09033 is good enough
        #deltal = math.radians(-0.09033 / 3600.0)
        deltalon = -4.379321981462438e-07
        lon += deltalon

    return lon


def rootbysecand(f, angle, x0, x1, precision=0.000000001):
    ''' solve the equation when function f(jd, angle) reaches zero by
    Secand method

    '''
    fx0, fx1 = f(x0, angle), f(x1, angle)
    while abs(fx1) > precision and abs(x0 - x1) > precision and fx0 != fx1:
        x2 = x1 - fx1 * (x1 - x0) / (fx1 - fx0)
        fx0 = fx1
        fx1 = f(x2, angle)
        x0 = x1
        x1 = x2
    return x1


def normrad(r):
    ''' covernt radian to 0 - 2pi '''
    alpha = fmod(r, TWOPI)
    if alpha < 0:
        alpha += TWOPI
    return alpha


def npitopi(r):
    ''' convert an angle in radians into (-pi, +pi] '''
    r = fmod(r, TWOPI)
    if r > PI:
        r -= TWOPI
    elif r <= -1.0 * PI:
        r += TWOPI
    return r


def f_solarangle(jd, r_angle):
    ''' Calculate the difference between target angle and solar geocentric
    longitude at a given JDTT

    and normalize the angle between Sun's Longitude on a given
    day and the angle we are looking for to (-pi, pi), therefore f(x) is
    continuous from -pi to pi, '''

    return npitopi(apparentsun(jd) - r_angle)


def f_msangle(jd, angle):
    ''' Calculate difference between target angle and current sun-moon angle

    Arg:
        jd: time in JDTT
    Return:
        angle in radians, convert to -pi to +pi range

        '''
    return npitopi(apparentmoon(jd, ignorenutation=True)
                 - apparentsun(jd, ignorenutation=True)
                 - angle)


def solarterm(year, angle):
    ''' calculate Solar Term by secand method

    The Sun's moving speed on ecliptical longitude is 0.04 argsecond / second,

    The accuracy of nutation by IAU2000B is 0.001"

    Args:
        year: the year in integer
        angle: degree of the solar term, in integer
    Return:
        time in JDTT

        '''

    # mean error when compare apparentsun to NASA(1900-2100) is 0.05"
    # 0.000000005 radians = 0.001"
    ERROR = 0.000000005

    r = normrad(math.radians(angle))
    # negative angle means we want search backward from Vernal Equinox,
    # initialize x0 to the day which apparent Sun longitude close to the angle
    # we searching for
    est_vejd = g2jd(year, 3, 20.5)
    x0 = est_vejd + angle * 360.0 / 365.24  # estimate
    x1 = x0 + 0.5

    return rootbysecand(f_solarangle, r, x0, x1, precision=ERROR)


def newmoon(jd):
    ''' search newmoon near a given date.

    Angle between Sun-Moon has been converted to [-pi, pi] range so the
    function f_msangle is continuous in that range. Use Secand method to find
    root.

    Test shows newmoon can be found in 5 iterations, if the start is close
    enough, it may use only 3 iterations.

    Arg:
        jd: in JDTT
    Return:
        JDTT of newmoon

    '''

    # 0.0000001 radians is about 0.02 arcsecond, mean error of apparentmoon
    # when compared to JPL Horizon is about 0.7 arcsecond
    ERROR = 0.0000001

    # initilize x0 to the day close to newmoon
    x0 = jd - f_msangle(jd, 0) / MOON_SPEED
    x1 = x0 + 0.5
    return rootbysecand(f_msangle, 0, x0, x1, precision=ERROR)


def findnewmoons(start, count=15):
    ''' search new moon from specified start time

    Arg:
        start: the start time in JD, doesn't matter if it is in TT or UT
        count: the number of newmoons to search after start time

    Return:
        a list of JDTT when newmoon occure

        '''
    nm = 0
    newmoons = []
    nmcount = 0
    count += 1
    while nmcount < count:
        b = newmoon(start)
        if b != nm:
            newmoons.append(b)
            nm = b
            nmcount += 1
            start = nm + SYNODIC_MONTH
        else:
            start += 1

    return newmoons


def apparentmoon(jde, ignorenutation=False):
    ''' calculate the apparent position of the Moon, it is an alias to the
    lea406 function'''
    return lea406_full(jde, ignorenutation)


def apparentsun(jde, ignorenutation=False):
    ''' calculate the apprent place of the Sun.
    Arg:
        jde as jde
    Return:
        geocentric longitude in radians, 0 - 2pi

        '''
    heliolong = vsop(jde)
    geolong = heliolong + PI

    # compensate nutation
    if not ignorenutation:
        geolong += nutation(jde)

    labbr = lightabbr_high(jde)
    geolong += labbr

    return normrad(geolong)


#------------------------------------------------------------------------------
# LEA-406 Moon Solution
#
# Reference:
#    Long-term harmonic development of lunar ephemeris.
#       Kudryavtsev S.M.  <Astron. Astrophys. 471, 1069 (2007)>
#
# the tables M_AMP, M_PHASE, M_ARG are imported from aa_full_table
#------------------------------------------------------------------------------
FRM = [785939.924268, 1732564372.3047, -5.279, .006665, -5.522e-5]
from aa_full_table import M_ARG, M_AMP, M_PHASE

# post import process of LEA-406 tables, horizontal split the numpy array
F0_V, F1_V, F2_V, F3_V, F4_V = np.hsplit(M_ARG, 5)
CV = M_PHASE * DEG2RAD
C_V, CT_V, CTT_V = np.hsplit(CV, 3)
A_V, AT_V, ATT_V = np.hsplit(M_AMP, 3)


def lea406_full(jd, ignorenutation=False):
    ''' compute moon ecliptic longitude using lea406
    numpy is used
    '''

    t = (jd - J2000) / 36525.0
    t2 = t * t
    t3 = t2 * t
    t4 = t3 * t

    tm = t / 10.0
    tm2 = tm * tm

    V = FRM[0] + (((FRM[4] * t + FRM[3]) * t + FRM[2]) * t + FRM[1]) * t

    # numpy array operation
    ARGS = ne.evaluate('''( F0_V
                          + F1_V * t
                          + F2_V * t2
                          + F3_V * t3
                          + F4_V * t4) * ASEC2RAD''')

    P = ne.evaluate('''(  A_V   * sin(ARGS + C_V)
                        + AT_V  * sin(ARGS + CT_V)  * tm
                        + ATT_V * sin(ARGS + CTT_V) * tm2)''')
    V += sum(P)
    V = V * ASEC2RAD

    if not ignorenutation:
        V += nutation(jd)
    return normrad(V)


def main():
    #jd = 2444239.5
    jd = g2jd(1900, 1, 1)
    for i in range(10):
        l = normrad(lea406_full(jd))
        #d = fmtdeg(math.degrees(npitopi(e -l )))
        print(jd, l, fmtdeg(math.degrees(l)))
        jd += 2000
    #print fmtdeg(math.degrees(e) % 360.0)
    #angle = -105
    #while angle < 360:
    #    a = solarterm(2014, angle)
    #    print 'search %d %s' % (angle,jdftime(a, tz=8, ut=True))
    #    angle += 15

if __name__ == "__main__":
    main()
