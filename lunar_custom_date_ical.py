#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
This script generates an iCalendar file containing events on specific lunar dates.
这个脚本生成一个包含特定农历日期事件的iCalendar文件。
useful for tracking lunar birthdays, anniversaries, ganji dates, etc.
适用于追踪农历生日，纪念日，赶集日等
'''

__license__ = 'BSD'
__copyright__ = '2020, Chen Wei <weichen302@gmail.com>'
__version__ = '0.0.3'

from io import StringIO
from datetime import datetime
from datetime import timedelta
import getopt
import gzip
import os
import re
import sqlite3
import sys
import urllib.request
import zlib
from lunarcalbase import cn_lunarcal

APPDIR = os.path.abspath(os.path.dirname(__file__))
DB_FILE = os.path.join(APPDIR, 'db', 'lunarcal.sqlite')
RE_CAL = re.compile('(\d{4})年(\d{1,2})月(\d{1,2})日')
#PROXY = {'http': 'http://localhost:8001'}
PROXY = None
OUTPUT = os.path.join(APPDIR, 'chinese_lunar_custom_date_%s_%s.ics')

ICAL_HEAD = ('BEGIN:VCALENDAR\n'
             'PRODID:-//Chen Wei//Chinese Lunar Calendar//EN\n'
             'VERSION:2.0\n'
             'CALSCALE:GREGORIAN\n'
             'METHOD:PUBLISH\n'
             'X-WR-CALNAME:农历日期\n'
             'X-WR-TIMEZONE:Asia/Shanghai\n'
             'X-WR-CALDESC:中国农历自定义日期日程. 农历数据来自香港天文台')

ICAL_SEC = ('BEGIN:VEVENT\n'
            'X-MICROSOFT-CDO-BUSYSTATUS:FREE\n'
            'DTSTAMP:%s\n'
            'UID:%s\n'
            'DTSTART;VALUE=DATE:%s\n'
            'DTEND;VALUE=DATE:%s\n'
            'STATUS:CONFIRMED\n'
            'SUMMARY:%s\n'
            'END:VEVENT')

ICAL_END = 'END:VCALENDAR'

CN_DAY = {'初二': 2, '初三': 3, '初四': 4, '初五': 5, '初六': 6,
          '初七': 7, '初八': 8, '初九': 9, '初十': 10, '十一': 11,
          '十二': 12, '十三': 13, '十四': 14, '十五': 15, '十六': 16,
          '十七': 17, '十八': 18, '十九': 19, '二十': 20, '廿一': 21,
          '廿二': 22, '廿三': 23, '廿四': 24, '廿五': 25, '廿六': 26,
          '廿七': 27, '廿八': 28, '廿九': 29, '三十': 30}

CN_MON = {'正月': 1, '二月': 2, '三月': 3, '四月': 4,
          '五月': 5, '六月': 6, '七月': 7, '八月': 8,
          '九月': 9, '十月': 10, '十一月': 11, '十二月': 12,

          '閏正月': 101, '閏二月': 102, '閏三月': 103, '閏四月': 104,
          '閏五月': 105, '閏六月': 106, '閏七月': 107, '閏八月': 108,
          '閏九月': 109, '閏十月': 110, '閏十一月': 111, '閏十二月': 112}

GAN = ('庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁', '戊', '己')
ZHI = ('申', '酉', '戌', '亥', '子', '丑',
       '寅', '卯', '辰', '巳', '午', '未')
SX = ('猴', '鸡', '狗', '猪', '鼠', '牛',
      '虎', '兔', '龙', '蛇', '马', '羊')




def query_db(query, args=(), one=False):
    ''' wrap the db query, fetch into one step '''
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv



def gen_cal_dates(start, end, dates,fp):
    ''' generate lunar calendar in iCalendar format.
    Args:
        start and end date in ISO format, like 2010-12-31
        verboseyuefen: if True, show month in every event entry
        fp: path to output file
    Return:
        none
        '''
    startyear = int(start[:4])
    endyear = int(end[:4])
    if startyear > 1900 and endyear < 2101:
        # use Lunar Calendar from HKO
        print('use Lunar Calendar from HKO')
        sql = ('select date, lunardate, holiday, jieqi from ical '
               'where date>=? and date<=? order by date')
        rows = query_db(sql, (start, end))
    else:
        # compute Lunar Calendar by astronomical algorithm
        print('compute Lunar Calendar by astronomical algorithm ')
        rows = []
        for year in range(startyear, endyear + 1):
            row = cn_lunarcal(year)
            rows.extend(row)

    
    oneday = timedelta(days=1)
    lines = [ICAL_HEAD]
    for r in rows:
        dt = datetime.strptime(r['date'], '%Y-%m-%d')

        if r['lunardate'] in list(CN_MON.keys()):
            date = '%s%s' % (r['lunardate'],"初一")
        else:
            date = '%s%s' % (lunarmonth(r['date']), r['lunardate'])
        
        if date in dates:
            for d in dates[date]:
                
                summary = d
                uid = '%s-%s-lc@infinet.github.io' % (r['date'], d)
                utcstamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
                line = ICAL_SEC % (utcstamp, uid, dt.strftime('%Y%m%d'),
                            (dt + oneday).strftime('%Y%m%d'), summary)
                lines.append(line)
    lines.append(ICAL_END)
    outputf = open(fp, 'w')
    outputf.write('\n'.join(lines))
    outputf.close()
    print('iCal lunar calendar from %s to %s saved to %s' % (start, end, fp))


def lunarmonth(isodate):
    '''find lunar month for a date'''
    sql = ('select lunardate from ical where lunardate like "%月" and '
           'date<=? order by date desc limit 1')
    row = query_db(sql, (isodate,), one=True)
    res = 'Unknown'
    if row:
        res = row[0]
    return res

def parse_dates(fp):
    '''parse dates from a file, return a list of tuples
    Args:
        fp: path to the file
    Return:
        a list of tuples, each tuple contains (date, lunardate)
    '''
    dates = {}
    with open(fp, 'r',encoding='utf-8') as f:
        for line in f:
            line = line.split(",")
            if len(line) != 2:
                continue
            if line[0] not in dates:
                dates[line[0]] = [line[1].strip(" \n")]
            else:
                dates[line[0]].append(line[1].strip(" \n"))
    return dates


def main():
    cy = datetime.today().year
    start = '%d-01-01' % (cy - 1)
    end = '%d-12-31' % (cy + 60)

    helpmsg = ('Usage: lunar_ical.py --start=startdate --end=enddate --jieqi --yuefen\n'
'Example: \n'
'\tlunar_ical.py --start=2013-10-31 --end=2015-12-31 --dates ./birthday.csv\n'
'Or,\n'
'\tlunar_ical.py without option will generate the calendar from previous year '
'to the end of 60 years later\n')

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h',
                                   ['start=', 'end=', 'dates=', 'help'])
    except getopt.GetoptError as err:
        print(str(err))
        print(helpmsg)
        sys.exit(2)

    for o, v in opts:
        if o == '--start':
            start = v
        elif o == '--end':
            end = v
        elif o == '--dates':
            dates = parse_dates(v)
        elif 'h' in o:
            sys.exit(helpmsg)

    if len(sys.argv) == 1:
        fp = OUTPUT % ('prev_year', 'next_year')
    else:
        fp = OUTPUT % (start, end)

    gen_cal_dates(start, end,dates, fp)


def verify_lunarcalendar():
    ''' verify lunar calendar against data from HKO'''
    start = 1949
    sql = 'select date, lunardate,jieqi from ical where date>=? and date<=?'
    while start < 2101:
        print('compare %d' % start)
        ystart = '%d-01-01' % start
        yend = '%d-12-31' % start
        res = query_db(sql, (ystart, yend))
        hko = []
        for x in res:
            if x[2]:
                hko.append((x[0], '%s %s' % (x[1], x[2])))
            else:
                hko.append((x[0], x[1]))

        aalc = cn_lunarcal(start)
        for i in range(len(aalc)):
            aaday, aaldate = aalc[i]['date'], aalc[i]['lunardate']
            if aalc[i]['jieqi']:
                aaldate = '%s %s' % (aalc[i]['lunardate'], aalc[i]['jieqi'])
            hkoday, hkoldate = hko[i]
            #print aaday, aaldate
            if aaday != hkoday or aaldate != hkoldate:
                print('AA %s %s, HKO %s %s' % (aaday, aaldate, hkoday,
                                               hkoldate))
        start += 1


if __name__ == "__main__":
    main()
    #verify_lunarcalendar()
