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



### iCalendar格式的中国农历 节气 及传统节日

iCalendar是一种通用的日历交换格式，很多软件和设备，比如google calendar, apple
calendar, thunderbird + lightning插件, iphone/ipad, 安卓都支持。

以前订过iCalendar格式农历日历，但慢慢地它们都停止了更新。所幸香港天文台上可以
找到从1901年到2100年间两百年的农历-公历对照表，也就是这里用到的数据。 

这个[链接][iCal]是覆盖前年、今年以及明年三年的日历，把它加入到你最常用的软件
就可以了。

苹果设备上应该是:
 设置 => 邮件、通讯录、日历 => 添加账户  => 日历 添加已订阅日历

如果在Mac的日历程序里订阅到iCloud，这个日历还可以自动推送到所有使用那个iCloud
账户的ios设备。





[Contact me](mailto: weichen302@gmail.com)

[iCal]: https://raw.github.com/infinet/lunar-calender/master/chinese_lunar_prev_year_next_year.ics
[Hong Kong Observatory]: http://gb.weather.gov.hk/gts/time/conversionc.htm
