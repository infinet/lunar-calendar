#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include "astro.h"
#include "lunarcalbase.h"

static char *CN_DAY[] = {
    "", "",
    "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九",
    "初十", "十一", "十二", "十三", "十四", "十五", "十六", "十七",
    "十八", "十九", "二十", "廿一", "廿二", "廿三", "廿四", "廿五",
    "廿六", "廿七", "廿八", "廿九", "三十"
};

static char *CN_MON[] = {
    "十二月",
    "正月", "二月", "三月", "四月", "五月",   "六月",
    "七月", "八月", "九月", "十月", "十一月", "十二月", /* index = 12 */
    "", "", "", "", "", "",                /* pad from index 13 to 18 */
    "閏十一月", "閏十二月", "閏正月", "閏二月", "閏三月", "閏四月",
    "閏五月",   "閏六月",   "閏七月", "閏八月", "閏九月", "閏十月",
    "閏十一月", "閏十二月"
};

/* solar term's angle + 120 / 15 */
static char *CN_SOLARTERM[] = {
    "小雪", "大雪", "冬至", "小寒", "大寒", "立春", "雨水", "驚蟄",
    "春分", "清明", "穀雨", "立夏", "小滿", "芒種", "夏至", "小暑",
    "大暑", "立秋", "處暑", "白露", "秋分", "寒露", "霜降", "立冬",
    "小雪", "大雪", "冬至"
};

/* 干支记年 */
static char *GAN[] = {
    "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "已"
};

static char *ZHI[] = {
    "申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"
};

static char *SX[] = {
    "猴", "鸡", "狗", "猪", "鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊"
};


static double newmoons[MAX_NEWMOONS];
static double solarterms[MAX_SOLARTERMS];
static int firstnm_offset;

static struct lunarcal_cache *cached_lcs[CACHESIZE];
static int cache_initialized = 0;  /* flag for initialized cache */
static int cachep = 0;  /* next free location in cache */
static int rewinded = 0;  /* cache rewinded? free pointers */


/* normalize Julian Day to midnight after adjust timezone and deltaT */
double normjd(double jd, double tz)
{
    double deltat, tmp, jd_i, jd_f;
    GregorianDate g;
    g = jd2g(jd);
    deltat = deltaT(g.year, g.month);
    tmp = jd + (tz * 3600.0 - deltat) / 86400.0;
    g = jd2g(tmp);
    jd_f = modf(tmp, &jd_i);
    if (jd_f >= 0.5)
        jd = jd_i + 0.5;
    else
        jd = jd_i - 0.5;
    return jd;
}


/* initialize cache storage */
void init_cache(void)
{
    if (cache_initialized)
        return;

    int i;
    struct lunarcal_cache *tmp;
    for (i = 0; i < CACHESIZE; i++) {
        tmp = (struct lunarcal_cache *) malloc(sizeof(struct lunarcal_cache));
        tmp->year = -1;
        tmp->len = -1;
        cached_lcs[i] = tmp;
    }
    cache_initialized = 1;
}

void cn_lunarcal(int year)
{
    int i, k, len1, len2;
    double ystart, yend;
    struct lunarcal *thisyear[MAX_DAYS];
    struct lunarcal *nextyear[MAX_DAYS];
    struct lunarcal *output[MAX_DAYS];
    init_cache();
    len1 = get_cached_lc(thisyear, year);
    len2 = get_cached_lc(nextyear, year + 1);

    /* combine lunar calendars from this and next year. Leapmonth close to the
     * end of Gregorian year can only be found by compute Lunar calendar of the
     * next year */
    ystart = g2jd(year, 1, 1.0);
    yend = g2jd(year, 12, 31.0);
    k = 0;

    for (i = 0; i < len1; i++) {
        if (thisyear[i]->jd >= ystart)
            output[k++] = thisyear[i];
    }
    for (i = 0; i < len2; i++) {
        if (nextyear[i]->jd <= yend)
            output[k++] = nextyear[i];
    }

    print_lunarcal(output, k);
}


int get_cache_index(int year)
{
    int i;
    for (i = 0; i < CACHESIZE; i++) {
        if (cached_lcs[i]->year == year)
            return i;
    }
    return -1;
}


int get_cached_lc(struct lunarcal *p[], int year)
{
    int i, k, len;
    double angle;
    double jd_nm, est_nm;

    if ((k = get_cache_index(year)) > -1) {
        for (i = 0; i < cached_lcs[k]->len; i++) {
            p[i] = cached_lcs[k]->lcs[i];
        }
        return i;
    }

    for (i = 0; i < MAX_SOLARTERMS; i++) {
        angle = (double) (i * 15 - 120);
        solarterms[i] = normjd(solarterm(year, angle), TZ_CN);
    }

    /* search 15 newmoons start 30 days before last Winter Solstice */
    est_nm = solarterms[2] - 30;
    for (i = 0; i < MAX_NEWMOONS; i++) {
        jd_nm = newmoon(est_nm);
        newmoons[i] = normjd(jd_nm, TZ_CN);
        est_nm = jd_nm + SYNODIC_MONTH;
    }

    /* fill in and mark each day with its lunar calendar year, month, day */
    len = mark_month_day(p);

    /* add to cache */
    if (cachep >= CACHESIZE) {
        cachep = 0;
        rewinded = 1;
    }

    if (rewinded)
        for (i = 0; i < len; i++) {
            free(cached_lcs[cachep]->lcs[i]);
        }

    for (i = 0; i < len; i++) {
        cached_lcs[cachep]->lcs[i] = p[i];
    }
    cached_lcs[cachep]->year = year;
    cached_lcs[cachep]->len = len;
    cachep++;

    return len;
}


/* mark month and day number, solarterms */
int mark_month_day(struct lunarcal *lcs[])
{
    int i, k, len, idx_lc_newyear;
    int leapmonth, month;
    double lc_start, lc_end, jd, month_day1;
    struct lunarcal *lc;
    GregorianDate g;

    len = 0;
    month = 11;
    month_day1 = 0;
    idx_lc_newyear = -1;
    leapmonth = find_leap();
    lc_start = newmoons[firstnm_offset];
    lc_end = solarterms[MAX_SOLARTERMS -1];
    jd = lc_start;
    while (jd < lc_end) {  /* fill in days into array lcs */
        /* scan for month jd belongs */
        for (i = firstnm_offset; i < MAX_NEWMOONS; i++) {
            if (jd < newmoons[i]) {
                month = 11 + i - 1 - firstnm_offset;
                month_day1 = newmoons[i - 1];
                break;
            }
        }

        /* adjust leapmonth */
        if (leapmonth > -1 && month == leapmonth) {
            month = (month - 1) % 12 + 20;  /* add offset 20 to distinguish */
        } else if (leapmonth > -1 && month > leapmonth) {
            month = (month - 1) % 12;
        } else {
            month %= 12;
        }

        lc = lcalloc(jd);
        lc->month = month;
        lc->day = (int) (jd - month_day1 + 1);
        if (lc->month == 1 && lc->day == 1)
            idx_lc_newyear = len;   /* found 正月初一 */

        lcs[len++] = lc;
        jd += 1.0;
    }

    /* mark lunar year */
    int lyear;
    g = jd2g(lcs[idx_lc_newyear]->jd);  /* 正月初一 in Gregorian */
    for (i = 0; i < len; i++) {
        if (i < idx_lc_newyear)
            lyear = g.year - 1;
        else
            lyear = g.year;

        lcs[i]->lyear = lyear;
    }


    /* modify days with solar terms */
    for (i = 0; i < MAX_SOLARTERMS - 1; i++) {
        if (solarterms[i] >= lc_start) {
            k = (int) (solarterms[i] - lc_start);
            if (lcs[k])
                lcs[k]->solarterm = i;
        }
    }
    return len;
}


int find_leap(void)
{
    /* count newmoons between two Winter Solstice */
    int nmcount, flag, leapmonth, i, n;
    nmcount = 0;
    for (i = 0; i < MAX_NEWMOONS; i++) {
        if (newmoons[i] > solarterms[2]
            && newmoons[i] <= solarterms[MAX_SOLARTERMS - 1])
            nmcount += 1;
    }

    /* first new moon of new year */
    for (i = 0; i < MAX_NEWMOONS; i++) {
        if (newmoons[i] > solarterms[2]) {
            firstnm_offset = i - 1;
            break;
        }
    }

    /* leap year has more than 12 newmoons between two Winter Solstice */
    if (nmcount > 12) {
        for (i = 1; i < MAX_NEWMOONS; i++) {
            flag = 0;
            for (n = 0; n < MAX_SOLARTERMS; n++) {
                /* the leap month is the first month which does NOT contain
                 * solar terms that is multiple of 30 degrees */
                if (solarterms[n] >= newmoons[i - 1]
                        && solarterms[n] < newmoons[i]
                        && n % 2 == 0)
                    flag = 1;
            }
            if (!flag) {
                leapmonth = 11 + i - 1 - firstnm_offset;
                return leapmonth;
            }
        }
    }

    return -1;
}


struct lunarcal *lcalloc(double jd)
{
    struct lunarcal *p;
    p = (struct lunarcal *) malloc(sizeof(struct lunarcal));
    if (p) {
        p->jd = jd;
        p->solarterm = -1;
        p->lyear = -1;
        p->month = -1;
        p->day = -1;
    }
    return p;
}


/* generate 干支年份, e.g. 丙申[猴] */
void ganzhi(char *buf, size_t buflen, int lyear)
{
    int idx_gan, idx_zhi, idx_sx;

    idx_gan = lyear % 10;
    idx_zhi = lyear % 12;
    idx_sx = idx_zhi;
    snprintf(buf, buflen, "%s%s[%s]", GAN[idx_gan], ZHI[idx_zhi], SX[idx_sx]);
}


/* chinese traditional holiday */
void holiday(char *buf, size_t buflen, int m, int d)
{
    char cn_hol[30] = "";
    if (m == 12 && d == 8)
        sprintf(cn_hol, "腊八");
    if (m == 1 && d == 1)
        sprintf(cn_hol, "春节");
    if (m == 1 && d == 15)
        sprintf(cn_hol, "元宵");
    if (m == 5 && d == 5)
        sprintf(cn_hol, "端午");
    if (m == 7 && d == 7)
        sprintf(cn_hol, "七夕");
    if (m == 7 && d == 15)
        sprintf(cn_hol, "中元");
    if (m == 8 && d == 15)
        sprintf(cn_hol, "中秋");
    if (m == 9 && d == 9)
        sprintf(cn_hol, "重阳");
    if (m == 10 && d == 15)
        sprintf(cn_hol, "下元");
    snprintf(buf, buflen, cn_hol);
}


void print_lunarcal(struct lunarcal *p[], int len)
{
    int i;
    char isodate[30], dtstart[30], dtend[30];
    char tmp[30];
    char gzyear[30];
    char cnholiday[30];
    char utcstamp[30];
    struct tm *utc_time;
    time_t t = time(NULL);

    utc_time = gmtime(&t);
    sprintf(utcstamp, "%04d%02d%02dT%02d%02d%02dZ",
            1900 + utc_time->tm_year, 1 + utc_time->tm_mon, utc_time->tm_mday,
            utc_time->tm_hour, utc_time->tm_min, utc_time->tm_sec);
    for (i = 0; i < len; i++) {
        jdftime(isodate, p[i]->jd, "%y-%m-%d", 0, 0);
        jdftime(dtstart, p[i]->jd, "%y%m%d", 0, 0);
        jdftime(dtend, p[i]->jd, "%y%m%d", 24, 0);
        if (p[i]->day == 1) {
            ganzhi(gzyear, 30, p[i]->lyear);
            sprintf(tmp, "%s%s", gzyear, CN_MON[p[i]->month]);
        } else {
            sprintf(tmp, "%s", CN_DAY[p[i]->day]);
        }

        if (p[i]->solarterm > -1)
            sprintf(tmp, "%s %s", tmp, CN_SOLARTERM[p[i]->solarterm]);

        holiday(cnholiday, 30, p[i]->month, p[i]->day);
        // temp fix for 除夕 and 寒食 (need to find a way to include them into the holiday function)
        if (p[i+1]->month == 1 && p[i+1]->day == 1)
            sprintf(cnholiday, "除夕");

        // solarterm 9 is 清明
        if (p[i+1]->solarterm == 9)
            sprintf(cnholiday, "寒食");

        sprintf(tmp, "%s %s", tmp, cnholiday);

        printf("BEGIN:VEVENT\n"
               "DTSTAMP:%s\n"
               "UID:%s-lc@infinet.github.io\n"
               "DTSTART;VALUE=DATE:%s\n"
               "DTEND;VALUE=DATE:%s\n"
               "STATUS:CONFIRMED\n"
               "SUMMARY:%s\n"
               "END:VEVENT\n", utcstamp, isodate, dtstart, dtend, tmp);
     }
}
