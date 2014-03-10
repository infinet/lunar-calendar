#!/usr/bin/env python
# -*- coding: utf-8 -*-

from aa_full import findnewmoons
from aa_full import solarterm
from aa_full import jdftime
from aa_full import jdptime

__all__ = ['cn_lunarcal']

LCSTARTMONTH = 11

CN_DAY = {2: u'初二',  3: u'初三',  4: u'初四',  5: u'初五',  6: u'初六',
          7: u'初七',  8: u'初八',  9: u'初九', 10: u'初十', 11: u'十一',
         12: u'十二', 13: u'十三', 14: u'十四', 15: u'十五', 16: u'十六',
         17: u'十七', 18: u'十八', 19: u'十九', 20: u'二十', 21: u'廿一',
         22: u'廿二', 23: u'廿三', 24: u'廿四', 25: u'廿五', 26: u'廿六',
         27: u'廿七', 28: u'廿八', 29: u'廿九', 30: u'三十'}

CN_MON = {1: u'正月',  2: u'二月',  3: u'三月',    4: u'四月',
          5: u'五月',  6: u'六月',  7: u'七月',    8: u'八月',
          9: u'九月', 10: u'十月', 11: u'十一月', 12: u'十二月',

         99: u'閏十一月', 100: u'閏十二月', 101: u'閏正月',
        102: u'閏二月',   103: u'閏三月',   104: u'閏四月',
        105: u'閏五月',   106: u'閏六月',   107: u'閏七月',
        108: u'閏八月',   109: u'閏九月',   110: u'閏十月',
        111: u'閏十一月', 112: u'閏十二月'}

CN_SOLARTERM = {-120: u'小雪',-105: u'大雪',
                 -90: u'冬至', -75: u'小寒', -60: u'大寒',
                 -45: u'立春', -30: u'雨水', -15: u'惊蛰',
                   0: u'春分',  15: u'清明',  30: u'谷雨',
                  45: u'立夏',  60: u'小满',  75: u'芒种',
                  90: u'夏至', 105: u'小暑', 120: u'大暑',
                 135: u'立秋', 150: u'处暑', 165: u'白露',
                 180: u'秋分', 195: u'寒露', 210: u'霜降',
                 225: u'立冬', 240: u'小雪', 255: u'大雪', 270: u'冬至'}

CN_SOLARTERM = {-120: u'小雪',-105: u'大雪',
                 -90: u'冬至', -75: u'小寒', -60: u'大寒',
                 -45: u'立春', -30: u'雨水', -15: u'驚蟄',
                   0: u'春分',  15: u'清明',  30: u'穀雨',
                  45: u'立夏',  60: u'小滿',  75: u'芒種',
                  90: u'夏至', 105: u'小暑', 120: u'大暑',
                 135: u'立秋', 150: u'處暑', 165: u'白露',
                 180: u'秋分', 195: u'寒露', 210: u'霜降',
                 225: u'立冬', 240: u'小雪', 255: u'大雪', 270: u'冬至'}


def find_astro(year):
    ''' find new moons and solar terms needed for calculate lunar calender
    Arg:
        year is a integer
    Return:
        list of dictionaries
            [ {date,
               newmoon/angle,
               placeholder for month }, ... ]

        '''

    # find all solar terms from -120 to +270 degree, negative angle means
    # search backward from Vernal Equinox
    solarterms = []
    angle = -120

    while angle <= 270:
        jdst = solarterm(year, angle)
        solarterms.append([jdst, angle])
        #print angle, jdftime(jdst, tz=8, ut=True)
        angle += 15

    # search 15 newmoons start 30 days before last Winter Solstice
    nms = findnewmoons(solarterms[1][0] - 30)
    aadays = [[x, 'newmoon'] for x in nms]
    aadays.extend(solarterms)
    aadays.sort()

    # normalize all Julian Day to midnight for later compare
    aadays = [(jdptime(jdftime(d[0], '%y-%m-%d', tz=8, ut=True), '%y-%m-%d'),
               d[1]) for d in aadays]
    astro = [{'date': d[0], 'astro': d[1], 'month': None} for d in aadays]
    return astro


def mark_lunarcal_month(clc):
    ''' scan and modify the Chinese Lunar Calendar Astro list for start/end of
    Chinese Lunar year and leapmonth'''
    nmcount = 0
    mname = -1
    leapyear = False
    i = 0

    # debug
    #for x in clc:
    #    print jdftime(x['date']), x['astro']

    # mark month number of newmoon
    while i < len(clc):
        if clc[i]['month'] is None and clc[i]['astro'] == 'newmoon':
            nmcount += 1
            mname += 1
            clc[i]['month'] = mname
        elif clc[i]['astro'] == -90:
            nmcount = 0
            mname = LCSTARTMONTH
            clc[i]['month'] = LCSTARTMONTH
            if (clc[i + 1]['astro'] == 'newmoon' and
                clc[i + 1]['date'] == clc[i]['date']):
                # the next newmoon is the same day, it will be the day 1 of
                # month 11. This newmoon doesn't included in leap year
                # compute.
                clc[i + 1]['month'] = LCSTARTMONTH
                lcstart = clc[i]['date']
            else:
                n = i - 1
                while n >= 0:
                    if clc[n]['astro'] == 'newmoon':
                        clc[n]['month'] = LCSTARTMONTH
                        lcstart = clc[n]['date']
                        break
                    n -= 1
        elif clc[i]['astro'] == 270:
            # lunar calendar year ends with Winter Solstice
            lcend = clc[i]['date']

            for d in clc[i + 1:]:
                if d['date'] == clc[i]['date'] and d['astro'] == 'newmoon':
                    nmcount += 1
                    break
            # if there are more than 12 newmoons between two Winter
            # Solstice, it is a leap year
            if nmcount > 12:
                leapyear = True
        i += 1

    # mark month number for rest of days
    mname = -1
    for i in xrange(len(clc)):
        if clc[i]['month']:
            mname = clc[i]['month']
            if i > 0 and clc[i - 1]['date'] == clc[i]['date']:
                clc[i - 1]['month'] = mname
        else:
            clc[i]['month'] = mname

    # trim to days between the newmoon mark the month last Winter Solstice
    # belongs, to this Winter Solstice(including)
    clc = [d for d in clc if d['date'] >= lcstart and d['date'] <= lcend]

    # scan for leap month
    leap = None
    if leapyear:
        # search leap month from LC 11, to next LC 11, which = 11 + 13
        for m in xrange(11, 25):
            foundleap = True
            for d in clc:
                if d['astro'] == 'newmoon':
                    continue
                if d['month'] == m and d['astro'] % 30 == 0:
                    foundleap = False
            if foundleap:
                leap = m
                break

        for d in clc:
            if d['month'] == leap:
                d['month'] += -1 + 100  # add 100 to distinguish leap month
            elif d['month'] > leap:
                d['month'] -= 1

    for d in clc:
        if d['month'] > 12:
            d['month'] -= 12

    return clc


def search_lunarcal(year):
    ''' search JieQi and Newmoon, step 1

    Arg:
        year: integer like 2014
    Return:
        a dictionary {ISODATE: Lunar Calendar Date in Chinese}
        start at last LC November
    '''

    clc = find_astro(year)
    clcmonth = mark_lunarcal_month(clc)
    ystart = clcmonth[0]['date']
    yend = clcmonth[-1]['date'] + 1


    #debug
    #print
    #for x in clcmonth:
    #    print jdftime(x['date']), x['astro'], x['date']

    FLAG_NEWMOON = 1
    FLAG_ST = 2
    output = {}
    while ystart < yend:
        flag = 0
        # scan the month ystart belongs
        for d in clcmonth:
            if d['date'] > ystart:
                break
            if d['astro'] == 'newmoon':
                monthstart = d['date']
                mname = d['month']

        # scan if the day happens to be the begining of month, or has ST, so we
        # can choose the output date format accordingly. The day will be month
        # name if it is the day 1 of a month; if it also has solarterm, then
        # the name of solarterm will be append to month name; if it is not day
        # 1 but has solarterm, then only solarterm will be displayed; if it is
        # not begining of the month, or has solarterm, then only the date will
        # be showed.

        for d in clcmonth:
            if d['date'] > ystart:
                break

            day = int(ystart + 1 - monthstart)

            # the day we looking for is in the solarterms and newmoon table
            if d['date'] == ystart:
                if d['astro'] == 'newmoon':
                    flag |= FLAG_NEWMOON
                else:
                    flag |= FLAG_ST
                    angle = d['astro']

        if flag == (FLAG_NEWMOON | FLAG_ST):
            label = '%s %s' % (CN_MON[mname], CN_SOLARTERM[angle])
        elif flag == FLAG_NEWMOON:
            label = CN_MON[mname]
        elif flag == FLAG_ST:
            label = '%s %s' % (CN_DAY[day],  CN_SOLARTERM[angle])
        else:
            #print fmtjde2ut(jd,ut=False), s, nm, day
            label = CN_DAY[day]

        output[ystart] = label
        ystart += 1

    return output


def cn_lunarcal(year):
    ''' to generate lunar calendar for year, the search should started from
    previous Winter Solstice to next year's Winter Solstic.

    Because there might be a leap month after this Winter Solstic, which can
    only be found by compute Calendar of next year, for example, 2033 has a
    leap 11, calendar for this and next year are computed and combined, then
    trim to fit into this year scale.

    '''

    cal0 = search_lunarcal(year)
    cal1 = search_lunarcal(year + 1)
    for k, v in cal1.iteritems():
        cal0[k] = v

    start = jdptime('%s-%s-%s' % (year, 1, 1), '%y-%m-%d')
    end = jdptime('%s-%s-%s' % (year, 12, 31), '%y-%m-%d')
    lc = []
    for jd, mname in cal0.iteritems():
        if jd >= start and jd <= end:
            lc.append((
               jdftime(jd, '%y-%m-%d', ut=False),
                mname))
    lc.sort()
    return lc


def main():
    #a = cn_lunarcal(2033)
    #for x in a:
        #print x[0], x[1]
    find_astro(1979)
    find_astro(2057)

if __name__ == "__main__":
    main()
