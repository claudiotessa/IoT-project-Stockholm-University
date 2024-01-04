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
import socket
import os

broker = "test.mosquitto.org"	# Broker 

pub_topic = "iotProject/sensors" #send data of sensor
sub_topic = ["iotProject/devices", "iotProject/files"]

# when connecting to mqtt do this;
def on_connect(client, userdata, flags, rc):
	if rc==0:
		print("Connection established. Code: "+str(rc))
		client.subscribe(pub_topic, qos=1)
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
# if command is to switch on or off message has to be structured like this
# {"cmd":"switch", "id": id number, "onoff": on\off status}
# if command is to send the log file of a specific powersocket it has to be structured like this in order to send it through FTP
# {"cmd":"getloglog", "id": id number, "host": host ip, "port": host port to connect, "separator": "<SEPARATOR>", "buffer": int buffersize }

def on_message(client, userdata, message): 
    data = str(message.payload.decode("utf-8"))
    print("message received ", data)
    print("\nmessage topic=",message.topic)
    print("\nmessage qos=",message.qos)
    print("\nmessage retain flag=",message.retain)
	
# Connect functions for MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_publish = on_publish
client.on_log = on_log
client.on_message= on_message

# Connect to MQTT 
print("Attempting to connect to broker " + broker)
client.connect(broker)
client.loop_forever()

client.publish(sub_topic[0], '{"cmd":"switch", "id": 1, "onoff": "on"}')
#client.publish(sub_topic[1], '{"cmd":"getloglog", "id": 1, "host": 192.168.1.124, "port": 5001, "separator": "<SEPARATOR>", "buffer": 4096 }')

while True:
    time.sleep(2.0)