#1698793200000
import random as r
import csv
import datetime

# tempo 1:30, 1,45 2
times=[5400000, 6300000, 7200000]
# ore 19 20 21
hours=[68400000,72000000,75600000]
# minuti 15 25 40 50
minutes=[900000,1500000,2400000,3000000]
#itero tra i giorni
f = open("11-2023detections1.csv", 'a')
# 1st nov 2023 00:00, 1st dec 2023 00:00 (not included), ms in 24hr
for day in range(1698793200000,1701385200000,86400000):
    t=r.choice(times)
    h=r.choice(hours)
    m=r.choice(minutes)
    #example for a washing machine
    for moment in range(0,86340000,2000):
        if moment>=h+m and moment<=h+m+t :
            w=r.randint(1000,1400)
        else :
            # fluctuating watt usage while not working
            w=r.randint(4,6)
            # floating point
            w+=r.randint(0,100)/100
        writer = csv.writer(f, lineterminator = '\n')
        date=day+moment
        # dateString=datetime.datetime.fromtimestamp(date / 1000)
        # dateString= dateString.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] #1,2023-12-17T15:24:52.944Z,1.2
        # dateString+="Z"
        writer.writerow(["1", date, str(w)])
print("done")
f.close()
