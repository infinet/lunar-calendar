### lunar calender

Google, Apple, and Microsoft used to provide Chinese Lunar Calender in iCalender
format, but most links were died over years. It is become hard to find a usable
Chinese Lunar Calendar for use with online and offline calendar apps.

The Chinese Lunar Calender is mostly based on the motion of the Moon. It is said
the motion of Moon is very hard to predict, especially on the long run. Luckily
[Hong Kong Observatory] has published a convertion table for the period from
1901 to 2100. It is the most trustworthy Lunar Calender I can find on the web so
far.


### License

This package is released under the terms and conditions of the BSD License, a
copy of which is include in the file COPYRIGHT.


### How to run

run `lunar_ical`, it will fetch data from Hong Kong Observatory, save the data
to a local sqlite database, then use that database to generate two ics files,
one for all days from 1901 to 2100, **Warning**, this file is huge, over 6M;
another is only cover 3 years, from the previous to the end of next year.

Try the Chinese Lunar Calendar by add this [link][iCal] to your favorite calendar app.



[Contact me](mailto: weichen302@gmail.com)

[iCal]: https://raw.github.com/infinet/lunar-calender/master/chinese_lunar_prev_year_next_year.ics
[Hong Kong Observatory]: http://gb.weather.gov.hk/gts/time/conversionc.htm
