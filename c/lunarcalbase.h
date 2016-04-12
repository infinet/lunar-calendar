#define MAX_SOLARTERMS 27
#define MAX_NEWMOONS 15
#define MAX_DAYS 450
#define CACHESIZE 3
#define TZ_CN 8

struct lunarcal {
    double jd;
    int solarterm;    /* index of solarterm */
    int lyear;        /* year in Lunar Calendar */
    int month;        /* month in Lunar Calendar */
    int day;          /* day in Lunar Calendar */
    int holiday;      /* index of CN_HOLIDAY, -1 if not a traditional Holiday */
};

struct lunarcal_cache {  /* the item in cache */
    int year;
    int len;             /* days count of this cached lunar calendar */
    struct lunarcal *lcs[MAX_DAYS];   /* the cached lunar calendar */
};

/* Function prototypes */
void cn_lunarcal(int year);

int get_cached_lc(struct lunarcal *p[], int year);

double normjd(double jd, double tz);

int find_leap(void);

int mark_month_day(struct lunarcal *lcs[]);

void ganzhi(char *buf, size_t buflen, int lyear);

void mark_holiday(struct lunarcal *lcs[], int len);

struct lunarcal *lcalloc(double jd);

void print_lunarcal(struct lunarcal *p[], int len);

int get_cache_index(int year);

void init_cache(void);
