import random
from datetime import datetime, timedelta as td

d1 = datetime(2015, 1, 1, 0, 0, 0)
d2 = datetime(2015, 5, 31, 0, 0, 0)

delta = d2 - d1

print "time,count"
for i in range(delta.days * 24 + 1):
    count = int(random.paretovariate(2) - 1)
    if count:
        print "{},{}".format(d1 + td(hours=i), count)
