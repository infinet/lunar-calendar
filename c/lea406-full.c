/*
 copyright 2020, Chen Wei <weichen302@gmail.com>
 version 0.0.3
Implement astronomical algorithms for finding solar terms and moon phases.

Truncated LEA-406 for calculate Moon's apparent longitude;

Reference:
    LEA-406: S. M. Kudryavtsev (2007) "Long-term harmonic development of
             lunar ephemeris", Astronomy and Astrophysics 471, 1069-1075
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <pthread.h>
#include <assert.h>
#include "astro.h"
#include "lea406-full.h"

static double vlea406[MAX_THREADS];
static int num_threads = 0;  /* number of threads for compute lea406-full */
static int nelems_per_thread;   /* number of elements assigned to a thread */

/* count logical CPU by parsing /proc/cpuinfo */
int cpucount(void)
{
    FILE *fp;
    int logic_cpu;
    char *s;
    char buf[MAX_CPUINFO_LEN];
    fp = fopen("/proc/cpuinfo", "rb");
    logic_cpu = 0;
    while ((s = fgets(buf, MAX_CPUINFO_LEN, fp)) != NULL) {
        if (s == strstr(buf, "processor"))
            logic_cpu += 1;
    }
    logic_cpu = (logic_cpu > MAX_THREADS) ? MAX_THREADS : logic_cpu;
    return logic_cpu;
}


/* the thread worker for lea406 */
void *lea406worker(void *args)
{
    int tid, i, start, end;
    double t, tm, tm2, V, arg;
    tid = ((struct worker_param *) args)->tid;
    t =   ((struct worker_param *) args)->tc;
    tm = t / 10.0;
    tm2 = tm * tm;

    start = tid * nelems_per_thread;
    end = start + nelems_per_thread;
    end = (end > LEA406TERMS) ? LEA406TERMS : end;

    V = 0.0;
    for (i = start; i < end; i++) {
        arg = (M_ARG[i][0] + t * (M_ARG[i][1] + M_ARG[i][2] * t)) * ASEC2RAD;
        V +=    M_AP[i][0] * sin(arg + M_AP[i][3] * DEG2RAD)
              + M_AP[i][1] * sin(arg + M_AP[i][4] * DEG2RAD) * tm
              + M_AP[i][2] * sin(arg + M_AP[i][5] * DEG2RAD) * tm2;
    }

    vlea406[tid] = V;
    return NULL;
}


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
    int rc, i;
    double t, V;
    t = (jd - J2000) / 36525.0;

    /* set number of threads number of logical CPU */
    num_threads = (num_threads) ? num_threads : cpucount();
    pthread_t threads[num_threads];
    struct worker_param *tmp;
    struct worker_param *thread_args[num_threads];
    /* init thread args */
    for (i = 0; i < num_threads; i++) {
        tmp = (struct worker_param *) malloc(sizeof(struct worker_param));
        tmp->tc = (jd - J2000) / 36525.0;
        tmp->tid = i;
        thread_args[i] = tmp;
    }

    nelems_per_thread = LEA406TERMS / num_threads;
    for (i = 0; i < num_threads; i++) {
        rc = pthread_create(&threads[i], NULL, lea406worker, thread_args[i]);
        assert(0 == rc);
    }

    V = FRM[0] + (((FRM[4] * t + FRM[3]) * t + FRM[2]) * t + FRM[1]) * t;
    for (i = 0; i < num_threads; i++) {
        rc = pthread_join(threads[i], NULL);
        assert(0 == rc);
    }

    for (i = 0; i < num_threads; i++) {
        V += vlea406[i];
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
