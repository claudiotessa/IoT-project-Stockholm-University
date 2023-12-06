## library file containing the function to get and log the wattage
##for now it will contain also the loop to gather data

import requests
import csv
import json

def getWattage():

    url = "http://127.0.0.1:4000"
    myobj = {'pi': "broker"}

    x = requests.post(url, json = myobj)
    print(x.text)
    y = json.loads(x.text)
    f = open('detections.csv', 'w')
    writer = csv.writer(f)
    writer.writerow([y["date"], str(y["wattage"])])
    f.close()
    
getWattage()