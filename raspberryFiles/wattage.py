## library file containing the function to get and log the wattage
##for now it will contain also the loop to gather data

import requests
import csv
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import subprocess

# Set MQTT broker and topic
broker = "test.mosquitto.org"	# Broker 

pub_topic = "iotProject/sensors" #send data of sensor
sub_topic = ["iotProject/devices", "iotProject/file"] #control for the change in the actuator status
############### Sensor section ##################
def get_wattage():

    url = "http://127.0.0.1:4000" #change depending on who is being the simulator
    myobj = {'pi': "broker"}

    x = requests.post(url, json = myobj)
    #print(x.text)
    y = json.loads(x.text)
    f = open('detections.csv', 'a')
    writer = csv.writer(f, lineterminator = '\n')
    writer.writerow([y["date"], str(y["wattage"])])
    f.close()
    return y

############### MQTT section ##################

# when connecting to mqtt do this;
def on_connect(client, userdata, flags, rc):
	if rc==0:
		print("Connection established. Code: "+str(rc))
	else:
		print("Connection failed. Code: " + str(rc))
		
def on_publish(client, userdata, mid):
    print("Published: " + str(mid))
	
def on_disconnect(client, userdata, rc):
	if rc != 0:
		print ("Unexpected disonnection. Code: ", str(rc))
	else:
		print("Disconnected. Code: " + str(rc))
	
def on_log(client, userdata, level, buf):		# Message is in buf
    print("MQTT Log: " + str(buf))

#when getting message from a subscribed topic 
# {"cmd":"switch", "id": id number, "onoff": on\off status}
# {"cmd":"getloglog", "id": id number}

def on_message(client, userdata, message): 
    data = str(message.payload.decode("utf-8"))
    print("message received " ,)
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)
    try:
        dictCommand = json.loads(data)
        if dictCommand["cmd"] == "switch" :
            subprocess.run(["tdtool", "--"+dictCommand["onoff"], dictCommand["id"]])
        #elif dictCommand["cmd"] == "getlog" :
    except ValueError as error:
        return error
	
# Connect functions for MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_publish = on_publish
client.on_log = on_log
client.on_message= on_message

# Connect to MQTT 
print("Attempting to connect to broker " + broker)
client.connect(broker)	# Broker address, port and keepalive (maximum period in seconds allowed between communications with the broker)
for i in sub_topic :
    client.subscribe(i)
client.loop_start()

# Loop that publishes message
while True:
	data_to_send = get_wattage()
	client.publish(pub_topic, str(data_to_send))
	time.sleep(2.0)	# Set delay