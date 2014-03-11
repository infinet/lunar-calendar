#!/usr/bin/env python
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
__copyright__ = '2014, Chen Wei <weichen302@gmail.com>'
__version__ = '0.0.3'

from numpy import *
import numexpr as ne
from aa_full_table import *

J2000 = 2451545.0
SYNODIC_MONTH = 29.53
MOON_SPEED = 2 * pi / SYNODIC_MONTH
TROPICAL_YEAR = 365.24
SUN_SPEED = 2 * pi / TROPICAL_YEAR
ASEC2RAD = 4.848136811095359935899141e-6
DEG2RAD = 0.017453292519943295
ASEC360 = 1296000.0
PI = pi
TWOPI = 2 * pi

# post import process of LEA-406 tables
# horizontal split the numpy array
F0_V, F1_V, F2_V, F3_V, F4_V = hsplit(M_ARG, 5)
CV = M_PHASE * DEG2RAD
C_V, CT_V, CTT_V = hsplit(CV, 3)
A_V, AT_V, ATT_V = hsplit(M_AMP, 3)


# 77 terms IAU2000B Luni-Solar nutation table from USNO NOVAS c source
#
# Luni-Solar argument multipliers,  coefficients, unit 1e-7 arcsec
# L  L'  F  D  Om longitude (sin, t*sin, cos), obliquity (cos, t*cos, sin)
IAU2000BNutationTable = array([
    [  0,  0,  0,  0, 1, -172064161, -174666,  33386, 92052331,  9086, 15377 ],
    [  0,  0,  2, -2, 2,  -13170906,   -1675, -13696,  5730336, -3015, -4587 ],
    [  0,  0,  2,  0, 2,   -2276413,    -234,   2796,   978459,  -485,  1374 ],
    [  0,  0,  0,  0, 2,    2074554,     207,   -698,  -897492,   470,  -291 ],
    [  0,  1,  0,  0, 0,    1475877,   -3633,  11817,    73871,  -184, -1924 ],
    [  0,  1,  2, -2, 2,    -516821,    1226,   -524,   224386,  -677,  -174 ],
    [  1,  0,  0,  0, 0,     711159,      73,   -872,    -6750,     0,   358 ],
    [  0,  0,  2,  0, 1,    -387298,    -367,    380,   200728,    18,   318 ],
    [  1,  0,  2,  0, 2,    -301461,     -36,    816,   129025,   -63,   367 ],
    [  0, -1,  2, -2, 2,     215829,    -494,    111,   -95929,   299,   132 ],
    [  0,  0,  2, -2, 1,     128227,     137,    181,   -68982,    -9,    39 ],
    [ -1,  0,  2,  0, 2,     123457,      11,     19,   -53311,    32,    -4 ],
    [ -1,  0,  0,  2, 0,     156994,      10,   -168,    -1235,     0,    82 ],
    [  1,  0,  0,  0, 1,      63110,      63,     27,   -33228,     0,    -9 ],
    [ -1,  0,  0,  0, 1,     -57976,     -63,   -189,    31429,     0,   -75 ],
    [ -1,  0,  2,  2, 2,     -59641,     -11,    149,    25543,   -11,    66 ],
    [  1,  0,  2,  0, 1,     -51613,     -42,    129,    26366,     0,    78 ],
    [ -2,  0,  2,  0, 1,      45893,      50,     31,   -24236,   -10,    20 ],
    [  0,  0,  0,  2, 0,      63384,      11,   -150,    -1220,     0,    29 ],
    [  0,  0,  2,  2, 2,     -38571,      -1,    158,    16452,   -11,    68 ],
    [  0, -2,  2, -2, 2,      32481,       0,      0,   -13870,     0,     0 ],
    [ -2,  0,  0,  2, 0,     -47722,       0,    -18,      477,     0,   -25 ],
    [  2,  0,  2,  0, 2,     -31046,      -1,    131,    13238,   -11,    59 ],
    [  1,  0,  2, -2, 2,      28593,       0,     -1,   -12338,    10,    -3 ],
    [ -1,  0,  2,  0, 1,      20441,      21,     10,   -10758,     0,    -3 ],
    [  2,  0,  0,  0, 0,      29243,       0,    -74,     -609,     0,    13 ],
    [  0,  0,  2,  0, 0,      25887,       0,    -66,     -550,     0,    11 ],
    [  0,  1,  0,  0, 1,     -14053,     -25,     79,     8551,    -2,   -45 ],
    [ -1,  0,  0,  2, 1,      15164,      10,     11,    -8001,     0,    -1 ],
    [  0,  2,  2, -2, 2,     -15794,      72,    -16,     6850,   -42,    -5 ],
    [  0,  0, -2,  2, 0,      21783,       0,     13,     -167,     0,    13 ],
    [  1,  0,  0, -2, 1,     -12873,     -10,    -37,     6953,     0,   -14 ],
    [  0, -1,  0,  0, 1,     -12654,      11,     63,     6415,     0,    26 ],
    [ -1,  0,  2,  2, 1,     -10204,       0,     25,     5222,     0,    15 ],
    [  0,  2,  0,  0, 0,      16707,     -85,    -10,      168,    -1,    10 ],
    [  1,  0,  2,  2, 2,      -7691,       0,     44,     3268,     0,    19 ],
    [ -2,  0,  2,  0, 0,     -11024,       0,    -14,      104,     0,     2 ],
    [  0,  1,  2,  0, 2,       7566,     -21,    -11,    -3250,     0,    -5 ],
    [  0,  0,  2,  2, 1,      -6637,     -11,     25,     3353,     0,    14 ],
    [  0, -1,  2,  0, 2,      -7141,      21,      8,     3070,     0,     4 ],
    [  0,  0,  0,  2, 1,      -6302,     -11,      2,     3272,     0,     4 ],
    [  1,  0,  2, -2, 1,       5800,      10,      2,    -3045,     0,    -1 ],
    [  2,  0,  2, -2, 2,       6443,       0,     -7,    -2768,     0,    -4 ],
    [ -2,  0,  0,  2, 1,      -5774,     -11,    -15,     3041,     0,    -5 ],
    [  2,  0,  2,  0, 1,      -5350,       0,     21,     2695,     0,    12 ],
    [  0, -1,  2, -2, 1,      -4752,     -11,     -3,     2719,     0,    -3 ],
    [  0,  0,  0, -2, 1,      -4940,     -11,    -21,     2720,     0,    -9 ],
    [ -1, -1,  0,  2, 0,       7350,       0,     -8,      -51,     0,     4 ],
    [  2,  0,  0, -2, 1,       4065,       0,      6,    -2206,     0,     1 ],
    [  1,  0,  0,  2, 0,       6579,       0,    -24,     -199,     0,     2 ],
    [  0,  1,  2, -2, 1,       3579,       0,      5,    -1900,     0,     1 ],
    [  1, -1,  0,  0, 0,       4725,       0,     -6,      -41,     0,     3 ],
    [ -2,  0,  2,  0, 2,      -3075,       0,     -2,     1313,     0,    -1 ],
    [  3,  0,  2,  0, 2,      -2904,       0,     15,     1233,     0,     7 ],
    [  0, -1,  0,  2, 0,       4348,       0,    -10,      -81,     0,     2 ],
    [  1, -1,  2,  0, 2,      -2878,       0,      8,     1232,     0,     4 ],
    [  0,  0,  0,  1, 0,      -4230,       0,      5,      -20,     0,    -2 ],
    [ -1, -1,  2,  2, 2,      -2819,       0,      7,     1207,     0,     3 ],
    [ -1,  0,  2,  0, 0,      -4056,       0,      5,       40,     0,    -2 ],
    [  0, -1,  2,  2, 2,      -2647,       0,     11,     1129,     0,     5 ],
    [ -2,  0,  0,  0, 1,      -2294,       0,    -10,     1266,     0,    -4 ],
    [  1,  1,  2,  0, 2,       2481,       0,     -7,    -1062,     0,    -3 ],
    [  2,  0,  0,  0, 1,       2179,       0,     -2,    -1129,     0,    -2 ],
    [ -1,  1,  0,  1, 0,       3276,       0,      1,       -9,     0,     0 ],
    [  1,  1,  0,  0, 0,      -3389,       0,      5,       35,     0,    -2 ],
    [  1,  0,  2,  0, 0,       3339,       0,    -13,     -107,     0,     1 ],
    [ -1,  0,  2, -2, 1,      -1987,       0,     -6,     1073,     0,    -2 ],
    [  1,  0,  0,  0, 2,      -1981,       0,      0,      854,     0,     0 ],
    [ -1,  0,  0,  1, 0,       4026,       0,   -353,     -553,     0,  -139 ],
    [  0,  0,  2,  1, 2,       1660,       0,     -5,     -710,     0,    -2 ],
    [ -1,  0,  2,  4, 2,      -1521,       0,      9,      647,     0,     4 ],
    [ -1,  1,  0,  1, 1,       1314,       0,      0,     -700,     0,     0 ],
    [  0, -2,  2, -2, 1,      -1283,       0,      0,      672,     0,     0 ],
    [  1,  0,  2,  2, 1,      -1331,       0,      8,      663,     0,     4 ],
    [ -2,  0,  2,  2, 2,       1383,       0,     -2,     -594,     0,    -2 ],
    [ -1,  0,  0,  0, 2,       1405,       0,      4,     -610,     0,     2 ],
    [  1,  1,  2, -2, 2,       1290,       0,      0,     -556,     0,     0 ]
])


def vsopLx(vsopterms, t):
    ''' helper function for calculate VSOP87 '''
    lx = vsopterms[:, 0] * cos(vsopterms[:, 1] + vsopterms[:, 2] * t)
    #for vsopterm in vsopterms:
    #    A = vsopterm[0]
    #    B = vsopterm[1]
    #    C = vsopterm[2]
    #    Lx += A * math.cos(B + C * t)
    return sum(lx)


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
    L0 = vsopLx(earth_L0, t)
    L1 = vsopLx(earth_L1, t)
    L2 = vsopLx(earth_L2, t)
    L3 = vsopLx(earth_L3, t)
    L4 = vsopLx(earth_L4, t)
    L5 = vsopLx(earth_L5, t)

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


def fmtdeg(fdegree):
    '''convert decimal degree to d m s format string'''
    if abs(fdegree) > 360:
        fdegree = math.fmod(fdegree, 360.0)
    degree = math.fabs(fdegree)
    tmp, deg = math.modf(degree)
    minutes = tmp * 60
    secs = math.modf(minutes)[0] * 60
    sign =''
    if fdegree < 0:
        sign = '-'
    res = '''%s%d%s%d'%.6f"''' % (sign, int(deg), u'\N{DEGREE SIGN}',
                            math.floor(minutes), secs)
    return res


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
        angle in radians, convert to -PI to + PI range

        '''
    return npitopi(apparentmoon(jd, ignorenutation=True)
                 - apparentsun(jd, ignorenutation=True)
                 - angle)


def solarterm(year, angle):
    ''' calculate Solar Term by secand method

    The Sun's moving speed on ecliptical longitude is 0.04 argsecond / second,

    The accuracy of abridged VSOP is 1", nutation by IAU2000B is 0.001"

    Args:
        year: the year in integer
        angle: degree of the solar term, in integer
    Return:
        time in JDTT

        '''

    # mean error when compare apparentsun to NASA(1900-2100) is 0.14"
    # 0.000000005 radians = 0.001"
    ERROR = 0.000000005

    r = normrad(math.radians(angle))
    # negative angle means we want search backward from Vernal Equinox,
    # initialize x0 to the day which apparent Sun longitude close to the angle
    # we searching for
    est_vejd = g2jd(year, 3, 20.5)
    x0 = est_vejd + angle * 360.0 / 365.24  # estimate
    #x0 -= solarangle(x0, r) / SUN_SPEED  # further closing
    x1 = x0 + 0.5

    return rootbysecand(f_solarangle, r, x0, x1, precision=ERROR)


def newmoon(jd):
    ''' search newmoon near a given date.

    Angle between Sun-Moon has been converted to [-pi, pi] range so the
    function msangle is continuous in that range. Use Secand method to find
    root.

    newmoon in 5 iterations, if the start is close enough, as the searching of
    next newmoon usualy does, it may use only 3 iterations.

    Arg:
        jd: in JDTT
    Return:
        JDTT of newmoon

    '''

    # 0.0000001 radians is about 0.02 arcsecond, mean error of apparentmoon
    # when compared to JPL Horizon is about 4 arcsecond
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
            if nm > 0 and abs(nm - b) > (SYNODIC_MONTH + 1):
                print 'last newmoon %s, found %s' % (fmtjde2ut(nm),
                                                     fmtjde2ut(b))
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
    return lea406(jde, ignorenutation)


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
    #print 'labbr = %s' % fmtdeg(math.degrees(labbr))
    geolong += labbr

    return normrad(geolong)


# the higher accuracy light abberation table from A & A.
# the first item of row is the power of time, the 3rd and 4th item are the arg
# of sin, they have been converted into radians.
LIGHTABBR_TABLE = [
    [ 0, 118.568,  1.527664004990,   6283.075850600876 ],
    [ 0,   2.476,  1.484508993906,  12566.151699456424 ],
    [ 0,   1.376,  0.486077687339,  77713.771468687730 ],
    [ 0,   0.119,  1.276490181677,   7860.419392621536 ],
    [ 0,   0.114,  5.885711004647,   5753.384884566103 ],
    [ 0,   0.086,  3.884055717388,  11506.769769132206 ],
    [ 0,   0.078,  2.841633387025, 161000.685738008644 ],
    [ 0,   0.054,  1.441333038870,  18849.227550057301 ],
    [ 0,   0.052,  2.993569534399,   3930.209696310768 ],
    [ 0,   0.034,  0.529208263814,  71430.695618086858 ],
    [ 0,   0.033,  2.091087703461,   5884.926847413107 ],
    [ 0,   0.023,  4.320419446313,   5223.693920276658 ],
    [ 0,   0.023,  5.674983441420,   5507.553238331428 ],
    [ 0,   0.021,  2.707426294193,  11790.629088932305 ],
    [ 1,   7.311,  5.819826570714,   6283.075850600876 ],
    [ 1,   0.305,  5.776715192860,  12566.151699456424 ],
    [ 1,   0.010,  5.733703298774,  18849.227550057301 ],
    [ 2,   0.309,  4.214128894867,   6283.075850600876 ],
    [ 2,   0.021,  3.578766215288,  12566.151699456424 ],
    [ 2,   0.004,  5.198655163283,  77713.771468687730 ],
    [ 3,   0.010,  2.700139544566,   6283.075850600876 ],
]


def lightabbr_high(jd):
    '''compute light abberation based on A & A p156
    the error will be less than 0.001"

    '''
    t = (jd - J2000) / 365250.0

    # variation of the Sun's longitude
    var_lon = 3548.330
    for r in LIGHTABBR_TABLE:
        var_lon += t ** r[0] * r[1] * sin(r[2] + r[3] * t)

    t = (jd - J2000) / 36525.0
    t2 = t * t
    t3 = t * t2

    # mean anomaly of the Sun
    M = 357.52910 + 35999.0503 * t - 0.0001559 * t2 - 0.00000048 * t3
    # the eccentricity of Earth's orbit
    e = 0.016708617 - 0.000042037 * t - 0.0000001236 * t2
    # Sun's equation of center
    C = ((1.9146 - 0.004817 * t - 0.000014 * t2) * sin(math.radians(M))
         + (0.019993 - 0.000101 * t) * sin(math.radians(2 * M))
         + 0.00029 * sin(math.radians(3 * M)))
    # true anomaly
    v = M + C
    # Sun's distance from the Earth, in AU
    R = (1.000001018 * (1 - e * e)) / (1 + e * cos(math.radians(v)))

    res = -0.005775518 * R * var_lon * ASEC2RAD

    return res


def g2jd(y, m, d):
    ''' convert a Gregorian date to JD
    from AA, p61
    '''

    if m <= 2:
        y -= 1
        m += 12
    a = int(y / 100)
    julian = False
    if y < 1582:
        julian = True
    elif y == 1582:
        if m < 10:
            julian = True
        if m == 10 and d <= 5:
            julian = True
        if m == 10 and d > 5 and d < 15:
            return 2299160.5
    if julian:
        b = 0
    else:
        b = 2 - a + int(a / 4)

    # 30.6001 is a hack Meeus suggested
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5


def td2jde(y, m, d):
    ''' convert Terrestrial (Dynamic) Time to JDE '''
    return g2jd(y, m ,d)


def ut2jde(y, m, d):
    ''' convert UT to JDE, compensate the delta T '''

    jd = g2jd(y, m, d)
    deltat = deltaT(y, m) / 86400.0
    return jd + deltat


def ut2jdut(y, m, d):
    ''' convert UT to JD, ignore delta T '''
    return g2jd(y, m, d)


def jdut2ut(jd):
    return jd2g(jd)


def jde2ut(jde, showtime=False):
    g = jd2g(jde, showtime)
    deltat = deltaT(g[0], g[1]) / 86400.0  # in day
    return jd2g(jde - deltat, showtime)


def jde2td(jde):
    return jd2g(jde)


def jd2g(jd):
    ''' convert JD to Gregorian date '''

    jd += 0.5
    z = int(jd)
    f = fmod(jd, 1.0)  # decimal part
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - int(alpha / 4)
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    res_d = b - d - int(30.6001 * e) + f
    if e < 14:
        res_m = e - 1
    else:
        res_m = e - 13
    if res_m > 2:
        res_y = c - 4716
    else:
        res_y = c - 4715
    return (res_y, res_m, res_d)


def jdptime(isodt, fmt, tz=0, ut=False):
    '''
    Args:
        isodt: datetime string in ISO format
        tz: a integer as timezone, e.g. -8 for UTC-8, 2 for UTC2
        fmt: like strftime but currently only support three format
             %y-%m-%d %H:%M:%S
             %y-%m-%d %H:%M
             %y-%m-%d
        ut: convert to UTC(adjust delta T)
    Return:
        Julian Day

    '''
    if fmt == '%y-%m-%d':
        isodate = isodt
        isot = '00:00:00'
    elif fmt == '%y-%m-%d %H:%M':
        isodate, isot = isodt.split()
        isot += ':00'
    else:
        isodate, isot = isodt.split()
    y, m, d = [int(x) for x in isodate.split('-')]
    #if isot:
    H, M, S = [int(x) for x in isot.split(':')]
    d += (H * 3600 + M * 60 + S) / 86400.0

    return g2jd(y, m, d)


def jdftime(jde, fmt='%y-%m-%d %H:%M:%S', tz=0, ut=False):
    ''' format a Julian Day to ISO format datetime

    Args:
        jde: time in JDTT
        tz: a integer as timezone, e.g. -8 for UTC-8, 2 for UTC2
        fmt: like strftime but currently only support three format
             %y-%m-%d %H:%M:%S
             %y-%m-%d %H:%M
             %y-%m-%d
        ut: convert to UTC(adjust delta T)

    Return:
        time string in ISO format, e.g. 1984-01-01 23:59:59

        '''

    g = jd2g(jde)
    deltat = deltaT(g[0], g[1]) if ut else 0

    # convert JDE to seconds, then adjust deltat
    utsec = jde * 86400.0 + tz * 3600 - deltat

    jdut = utsec / 86400.0

    # get time in seconds directly to minimize round error
    secs = (utsec + 43200) % 86400

    if fmt == '%y-%m-%d %H:%M':
        secs = int(round(secs / 60.0) * 60.0)
    else:
        secs = int(secs)
    if 86400 == secs:
        jdut = int(jdut) + 0.5
        secs = 0

    y, m, d = jd2g(jdut)
    d = int(d)

    # use integer math hereafter
    H = secs / 3600
    ms = secs % 3600
    M = ms / 60
    S = ms % 60

    # padding zero
    d = '0%d' % d if d < 10 else str(d)
    m = '0%d' % m if m < 10 else str(m)
    H = '0%d' % H if H < 10 else str(H)
    M = '0%d' % M if M < 10 else str(M)
    S = '0%d' % S if S < 10 else str(S)

    if fmt == '%y-%m-%d':
        isodt = '%d-%s-%s' % (y, m, d)
    elif fmt == '%y-%m-%d %H:%M':
        isodt = '%d-%s-%s %s:%s' % (y, m, d, H, M)
    else:
        isodt = '%d-%s-%s %s:%s:%s' % (y, m, d, H, M, S)

    return isodt


def deltaT(year, m ,d=0):
    ''' Polynomial Expressions for Delta T (ΔT) from nasa. Valid for -1999 to
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

    '''

    y = year + (m - 0.5) / 12
    if year < -500:
        u = (year - 1820) / 100.0
        return -20 + 32 * u ** 2
    elif year < 500:
        u = y / 100.0
        return  10583.6 + u * (-1014.41 +
                          u * (33.78311 +
                          u * (-5.952053 +
                          u * (-0.1798452 +
                          u * (0.022174192 +
                          u * 0.0090316521)))))
    elif year < 1600:
        u = (y -1000) / 100.0
        return  1574.2 + u * (-556.01 +
                         u * (71.23472 +
                         u * (0.319781 +
                         u * (-0.8503463 +
                         u * (-0.005050998 +
                         u * 0.0083572073)))))
    elif year < 1700:
        u = y -1600
        return 120 + u * (-0.9808 +
                     u * (- 0.01532 +
                     u / 7129))
    elif year < 1800:
        u = y - 1700
        return 8.83 + u * (0.1603 +
                        u * (-0.0059285 +
                        u * (0.00013336 +
                        u / -1174000)))
    elif year < 1860:
        u = y - 1800
        return 13.72 + u * (-0.332447 +
                        u * (0.0068612 +
                        u * (0.0041116 +
                        u * (-0.00037436 +
                        u * (0.0000121272 +
                        u * (-0.0000001699 +
                        u * 0.000000000875))))))
    elif year < 1900:
        u = y - 1860
        return 7.62 + u * (0.5737 +
                        u * (-0.251754 +
                        u * (0.01680668 +
                        u * (-0.0004473624 +
                        u / 233174))))
    elif year < 1920:
        u = y - 1900
        return -2.79 + u * (1.494119 +
                        u * (-0.0598939 +
                        u * (0.0061966 +
                        u * -0.000197)))
    elif year < 1941:
        u = y - 1920
        return 21.20 + u * (0.84493 +
                        u * (-0.076100 +
                        u * 0.0020936))
    elif year < 1961:
        u = y - 1950
        return 29.07 + u * (0.407 +
                        u * (-1.0 / 233 +
                        u / 2547))
    elif year < 1986:
        u = y - 1975
        return  45.45 + u * (1.067 +
                        u * (-1.0 / 260 +
                        u / -718))
    elif year < 2005:
        u = y -2000
        return 63.86 + u * (0.3345 +
                        u * (-0.060374 +
                        u * (0.0017275 +
                        u * (0.000651814 +
                        u * 0.00002373599))))
        '''
    else:
        # JPL uses "last known leap-second is used over any future interval" .
        # It causes the large error when compare apparent sun/moon position
        # with JPL Horizon

        return 67.182963
    '''
    elif year < 2050:
        u = y -2000
        return 62.92 + u * (0.32217 + u * 0.005589)
    elif year < 2150:
        u = (y - 1820.0) / 100.0
        return -20 + 32 * u ** 2 - 0.5628 * (2150 - y)
    else:
        u = (y - 1820.0) / 100.0
        return -20 + 32 * u ** 2


def nutation(jde):
    '''
    Calculate nutation angles using the IAU 2000B model.

    The table is from NOVAS(USNO) c source flle.

    "...the 77-term, IAU-approved truncated nutation series, IAU 2000B, which
    is accurate to about 0.001 arcsecond in the interval 1995-2050"

    Arg:
        jde as JDE
    Return:
        nutation of longitude in radians

    '''

    t = (jde - J2000) / 36525.0

    #Mean anomaly of the Moon, in arcsec
    L = 485868.249036 + t * 1717915923.2178

    #Mean anomaly of the Sun.
    Lp = 1287104.79305 + t * 129596581.0481

    #Mean argument of the latitude of the Moon.
    F = 335779.526232 + t * 1739527262.8478

    #Mean elongation of the Moon from the Sun.
    D = 1072260.70369 + t * 1602961601.2090

    #Mean longitude of the ascending node of the Moon.
    Om = 450160.398036 - t * 6962890.5431

    m1, m2, m3, m4, m5, AA, BB, CC, EE, DD, FF = hsplit(IAU2000BNutationTable,
                                                        11)
    args = (m1 * L + m2 * Lp + m3 * F + m4 * D + m5 * Om) * ASEC2RAD
    lon = sum((AA + BB * t) * sin(args) + CC * cos(args))

    # unit of longitude is 1.0e-7 arcsec, convert it to arcsec
    lon *= 1.0e-7

    # Constant account for the missing long-period planetary terms in the
    # truncated nutation model, in arcsec
    deplan = 0.000388
    lon += deplan

    lon *= ASEC2RAD  # Convert from arcsec to radians
    lon = fmod(lon, TWOPI)

    return lon


#------------------------------------------------------------------------------
# LEA-406 Moon Solution
#
# Reference:
#    Long-term harmonic development of lunar ephemeris.
#       Kudryavtsev S.M.  <Astron. Astrophys. 471, 1069 (2007)>
#
# the tables M_AMP, M_PHASE, M_ARG are imported from aa_full_table
#------------------------------------------------------------------------------
FRM = [785939.924268, 1732564372.3047, -5.279, .006665, -5.522e-5 ]


def lea406(jd, ignorenutation=False):
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
    for i in xrange(1):
        l = normrad(lea406(jd))
        #d = fmtdeg(math.degrees(npitopi(e -l )))
        print jd, l, fmtdeg(math.degrees(l))
        jd += 2000
    #print fmtdeg(math.degrees(e) % 360.0)
    #angle = -105
    #while angle < 360:
    #    a = solarterm(2014, angle)
    #    print 'search %d %s' % (angle,jdftime(a, tz=8, ut=True))
    #    angle += 15

if __name__ == "__main__":
    main()
