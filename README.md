### Chinese Lunar Calender

Google, Apple, and Microsoft used to provide Chinese Lunar Calender in iCalender
format, but most links were died over years. It is become hard to find a usable
Chinese Lunar Calendar for use with online and offline calendar apps.

The Chinese Lunar Calender is mostly based on the motion of the Moon. It is
said due to the complicate interaction, mostly from the Sun and the Earth, the
motion of Moon is very hard to predict, especially on the long run.  Luckily
[Hong Kong Observatory][HK_Obs] has published a convertion table for the period
from 1901 to 2100. It is the most trustworthy Lunar Calender I can find on the
web so far.

Lunar calendar beyond 1901-2100 range can also be generated. The
lunarcalbase.py uses VSOP87 planetary theory and LEA-406 lunar theory to
find solar terms and moon phases, then compute the calendar.

Both the full version and truncated version of LEA-406 and VSOP87 are included.
The full version is slightly slower. Their accuracy of finding apparent Sun and
Moon longitude compare to the DE431 based JPL Horizon are showed in following
figures.

![aa_full][]
![aa_trunc][]

For the time span from 1949 to 2100, lunar calendar created by above algorithm,
has only two discrepancies compare to the HKO's version: one is a solar term on
1979-01-20, the other is a new moon on 2057-09-29. It caused by few seconds of
error happens around midnight(UTC +8).

The official timezone before 1949 is slightly different than the current UTC +8
therefor the computed lunar calendar may not represent history accurately.


### License

This package is released under the terms and conditions of the BSD License, a
copy of which is include in the file COPYRIGHT.

**Hong Kong Observatory** has been very kind to provide and grant the permission
of using their convertion table, which is only for Non-Commercial use.

### How to run

run `lunar_ical`, it will fetch data from Hong Kong Observatory, save
the data to a local sqlite database, then use that database to generate a ics
file, which covers from the previous to the end of next year.

Try the Chinese Lunar Calendar by add this [ics file][iCal] to your favorite
calendar app.

start and end date can also be specified as command line options, for example

    `lunar_ical.py --start=1990-01-01 --end=2001-01-01`

The date must in ISO format.


### iCalendar格式的中国农历 节气 及传统节日

iCalendar是一种通用的日历交换格式，很多软件和设备，比如google calendar, apple
calendar, thunderbird + lightning插件, iphone/ipad, 安卓都支持。

以前订过iCalendar格式农历日历，但慢慢地它们都停止了更新。所幸香港天文台为公众提供了从1901年到2100年间两百年的农历-公历对照表，也就是这里用到的数据。

![Screenshot][]

下面是覆盖前年、今年以及明年三年的日历[ics文件][iCal]链接，把它加入到你最常用的软件就可以了。

[https://raw.github.com/infinet/lunar-calender/master/chinese_lunar_prev_year_next_year.ics][iCal]

苹果设备上应该是:
    设置 => 邮件、通讯录、日历 => 添加账户 => 其它 => 日历 添加已订阅日历

如果在Mac的*iCal*里订阅到iCloud，这个日历还可以自动推送到所有使用那个iCloud
账户的ios设备。



### 生成更长时段农历

如果需要更长时段的农历，可以下载`lunar_ical.py`

直接运行`./lunar_ical.py`会从香港天文台抓取1901到2100年间所有数据，然后生成上面
那个前后三年时段的农历ics文件；

使用参数--start和--end指定需要的起至日期, 例如:

    ./lunar_ical.py --start=2010-05-01 --end=2021-12-31


### 版权

本项目版权使用BSD协议，请参见所附COPYRIGHT文件。

感谢[香港天文台][HK_Obs]为公众提供并授权本项目使用其农历-公历对照数据，该部分数据仅限非商业用途。


[Contact me](mailto: weichen302@gmail.com)

[iCal]: https://raw.github.com/infinet/lunar-calender/master/chinese_lunar_prev_year_next_year.ics
[HK_Obs]: http://data.weather.gov.hk/gts/time/conversion1_text_c.htm
[Screenshot]: http://infinet.github.io/images/lunar_calendar.jpg
[aa_full]: http://infinet.github.io/images/moon-sun-full_lea406_vsop87_compare_JPL.png
[aa_trunc]: http://infinet.github.io/images/moon-sun-trunc_lea406_vsop87_compare_JPL.png
