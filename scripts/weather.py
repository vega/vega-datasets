import csv
import sys
import datetime

reader = csv.reader(sys.stdin)
headers = reader.next()


# WT14 - Drizzle
# WT03 - Thunder
# WT04 - Ice pellets, sleet, snow pellets, or small hail"
# WT05 - Hail (may include small hail)
# WT16 - Rain (may include freezing rain, drizzle, and freezing drizzle)"
# WT17 - Freezing rain
# WT18 - Snow, snow pellets, snow grains, or ice crystals
# WT08 - Smoke or haze
# WT11 - High or damaging winds
# WT22 - Ice fog or freezing fog
# WT01 - Fog, ice fog, or freezing fog (may include heavy fog)
# WT02 - Heavy fog or heaving freezing fog (not always distinguished from fog)
# WT13 - Mist

# AWND - Average daily wind speed (tenths of meters per second)
# TOBS - Temperature at the time of observation (tenths of degrees C)
# TMAX - Maximum temperature (tenths of degrees C)
# TMIN - Minimum temperature (tenths of degrees C)
# PRCP - Precipitation (tenths of mm)

names = ['DATE', 'PRCP', 'TMAX', 'TMIN', 'AWND', 'WEATHER']
writer = csv.DictWriter(sys.stdout, fieldnames=names, extrasaction='ignore')
# writer.writeheader()

sys.stdout.write('date,precipitation,temp_max,temp_min,wind,weather\n')

for row in reader:
    d = dict(zip(headers, row))

    d['WEATHER'] = 'sun'

    if d['WT22'] == '1' or d['WT02'] == '1' or d['WT01'] == '1':
        d['WEATHER'] = 'fog'

    if d['WT14'] == '1' or d['WT08'] == '1' or d['WT13'] == '1':
        d['WEATHER'] = 'drizzle'

    if d['WT16'] == '1' or d['WT17'] == '1' or d['WT05'] == '1' or d['WT03'] == '1':
        d['WEATHER'] = 'rain'

    if d['WT18'] == '1' or d['WT04'] == '1':
        d['WEATHER'] = 'snow'

    date = d['DATE']
    date = datetime.datetime.strptime(date, "%Y%m%d").strftime('%Y-%m-%d')
    d['DATE'] = date

    d['AWND'] = 1.0 * int(d['AWND'])/10
    d['TMAX'] = 1.0 * int(d['TMAX'])/10
    d['TMIN'] = 1.0 * int(d['TMIN'])/10
    d['PRCP'] = 1.0 * int(d['PRCP'])/10

    writer.writerow(d)
