#include <stdio.h>
#include <stdlib.h>
#include "lunarcalbase.h"


int main(int argc, char *argv[])
{
    int start, end;
    if (argc == 2) {
        start = atoi(argv[1]);
        end = start;
    } else if (argc == 3) {
        start = atoi(argv[1]);
        end = atoi(argv[2]);
    } else {
        printf("Usage: lunarcal startyear endyear \n");
        exit(2);
    }

    while (start <= end) {
        cn_lunarcal(start);
        start++;
    }

    return 0;
}
