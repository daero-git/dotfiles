import calendar
import datetime
import re

today = datetime.date.today()
cal = calendar.TextCalendar(firstweekday=6)
text = cal.formatmonth(today.year, today.month)

day_str = str(today.day)
highlight = (
    "${color ffb454}${font DejaVu Sans Mono:bold:size=9}"
    + day_str
    + "${font DejaVu Sans Mono:size=9}${color}"
)

text = re.sub(r"(?<!\d)" + day_str + r"(?!\d)", highlight, text, count=1)

for line in text.rstrip("\n").split("\n"):
    print("${alignc}" + line)
