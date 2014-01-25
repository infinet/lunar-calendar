#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''get lunar calendar from hk observatory '''

__license__ = 'BSD'
__copyright__ = '2014, Chen Wei <weichen302@gmail.com>'
__version__ = '0.0.1'


from StringIO import StringIO
from datetime import datetime
from datetime import timedelta
import cookielib
import gzip
import os
import re
import sqlite3
import urllib2
import zlib


APPDIR = os.path.abspath(os.path.dirname(__file__))
DB_FILE = os.path.join(APPDIR, 'db', 'lunarcal.sqlite')
RE_CAL = re.compile(u'(\d{4})年(\d{1,2})月(\d{1,2})日')
PROXY = {'http': 'http://localhost:8001'}
URL = 'http://gb.weather.gov.hk/gts/time/calendar/text/T%dc.txt'
OUTPUT = os.path.join(APPDIR, 'chinese_lunar_%s_%s.ics')

ICAL_HEAD = ('BEGIN:VCALENDAR\n'
             'PRODID:-//Chen Wei//Chinese Lunar Calendar//EN\n'
             'VERSION:2.0\n'
             'CALSCALE:GREGORIAN\n'
             'METHOD:PUBLISH\n'
             'X-WR-CALNAME:农历\n'
             'X-WR-TIMEZONE:Asia/Shanghai\n'
             'X-WR-CALDESC:中国农历1901-2100, 包括节气. 数据来自香港天文台')

ICAL_SEC = ('BEGIN:VEVENT\n'
            'DTSTART;VALUE=DATE:%s\n'
            'DTEND;VALUE=DATE:%s\n'
            'SUMMARY:%s\n'
            'END:VEVENT')

ICAL_END = 'END:VCALENDAR'


def initdb():
    try:
        print 'creating db dir'
        os.mkdir(os.path.join(APPDIR, 'db'))
    except OSError:
        pass

    conn = sqlite3.connect(DB_FILE)
    db = conn.cursor()
    db.execute('''CREATE TABLE IF NOT EXISTS ical (
                    id INTEGER PRIMARY KEY,
                    date TEXT UNIQUE,
                    lunardate TEXT,
                    jieqi TEXT)''')
    conn.commit()
    db.close()


def query_db(query, args=(), one=False):
    ''' wrap the db query, fetch into one step '''
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


class HTTPCompress(urllib2.BaseHandler):
    """A handler to add gzip capabilities to urllib2 requests """
    def http_request(self, req):
        req.add_header("Accept-Encoding", "gzip, deflate")
        req.add_header("User-Agent",
       "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.13) Gecko/20101203")
        return req

    def http_response(self, req, resp):
        old_resp = resp
        if resp.headers.get("content-encoding") == "gzip":
            data = gzip.GzipFile(fileobj=StringIO(resp.read()), mode="r")
            resp = urllib2.addinfourl(data, old_resp.headers,
                                      old_resp.url, old_resp.code)
            resp.msg = old_resp.msg
        if resp.headers.get("content-encoding") == "deflate":
            data = zlib.decompress(resp.read(), -zlib.MAX_WBITS)
            resp = urllib2.addinfourl(data, old_resp.headers,
                                      old_resp.url, old_resp.code)
            resp.msg = old_resp.msg
        return resp


def browser(proxy=None):
    gzip_support = HTTPCompress
    cj = cookielib.CookieJar()
    cookie_support = urllib2.HTTPCookieProcessor(cj)
    proxy_support = urllib2.ProxyHandler(proxy)
    if proxy:
        opener = urllib2.build_opener(gzip_support, urllib2.HTTPHandler,
                                     cookie_support, proxy_support)
    else:
        opener = urllib2.build_opener(gzip_support, urllib2.HTTPHandler,
                                                     cookie_support)
    return opener


def parse_hko(pageurl):
    ''' parse lunar calender from hk Obs
    Args: pageurl
    Return:
          a string contains all posts'''

    print 'grabbing and parsing %s' % pageurl
    br = browser(PROXY)
    lines = br.open(pageurl).readlines()
    sql_nojq = ('insert or replace into ical (date,lunardate) '
                'values(?,?) ')
    sql_jq = ('insert or replace into ical (date,lunardate,jieqi) '
              'values(?,?,?) ')
    conn = sqlite3.connect(DB_FILE)
    db = conn.cursor()
    for line in lines:
        line = line.decode('big5')
        m = RE_CAL.match(line)
        if m:
            fds = line.split()
            # add leading zero to month and day
            if len(m.group(2)) == 1:
                str_m = '0%s' % m.group(2)
            else:
                str_m = m.group(2)
            if len(m.group(3)) == 1:
                str_d = '0%s' % m.group(3)
            else:
                str_d = m.group(3)

            dt = '%s-%s-%s' % (m.group(1), str_m, str_d)
            if len(fds) > 3:  # last field is jieqi
                db.execute(sql_jq, (dt, fds[1], fds[3]))
            else:
                db.execute(sql_nojq, (dt, fds[1]))
    conn.commit()


def update_cal():
    ''' fetch lunar calendar from HongKong Obs, parse it and save to db'''
    for y in xrange(1901, 2101):
        parse_hko(URL % y)


def gen_cal(start, end, fp):
    ''' generate lunar calender in iCalendar format.
    Args:
        start and end date in ISO format, like 2010-12-31
        fp: path to output file
    Return:
        none
        '''

    sql = ('select date, lunardate, jieqi from ical '
           'where date>=? and date<=? order by date')
    rows = query_db(sql, (start, end))
    lines = [ICAL_HEAD]
    oneday = timedelta(days=1)
    for r in rows:
        dt = datetime.strptime(r['date'], '%Y-%m-%d')
        if r['jieqi']:
            ld = '%s %s' % (r['lunardate'], r['jieqi'])
        else:
            ld = r['lunardate']
        line = ICAL_SEC % (dt.strftime('%Y%m%d'),
                           (dt + oneday).strftime('%Y%m%d'), ld)
        lines.append(line.encode('utf8'))
    lines.append(ICAL_END)
    outputf = open(fp, 'w')
    outputf.write('\n'.join(lines))
    outputf.close()
    print 'iCal lunar calendar from %s to %s saved to %s' % (start, end, fp)


def main():
    if not os.path.exists(DB_FILE):
        initdb()
        update_cal()
    cy = datetime.today().year
    start = '%d-01-01' % (cy - 1)
    end = '%d-12-31' % (cy + 1)
    fp = OUTPUT % ('prev_year', 'next_year')
    gen_cal(start, end, fp)

    # from 1901 to 2100
    start2 = '1901-01-01'
    end2 = '2100-12-31'
    fp2 = OUTPUT % ('1901', '2100')
    gen_cal(start2, end2, fp2)


if __name__ == "__main__":
    main()
