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

# Set MQTT broker and topic
broker = "test.mosquitto.org"	# Broker 

pub_topic = "iotProject/sensors" #send data of sensor
sub_topic = ["iotProject/devices", "iotProject/files"] #control for the change in the actuator status

# logfile directory
csvfile = 'detections.csv'

#actuator dictionary for now just 1 dict, later will be a class that will index and manage multiple actuators
actuator_dict = {"date": None, "wattage": 1.2, "onoff": "on"}

############### Sensor section ##################

def get_wattage():
    url = "http://192.168.1.124:4000" #change depending on who is being the simulator
    myobj = {'pi': "broker"}
    x = requests.post(url, json = myobj)
    print("writing to file: ", x.text)
    y = json.loads(x.text)
    f = open(csvfile, 'a')
    writer = csv.writer(f, lineterminator = '\n')
    writer.writerow([str(y["id"]), y["date"], str(y["wattage"])])
    f.close()
    return y

############### FTP section ##################

def send_file(file, host, port, separator="<SEPARATOR>", buffersize=4096) :
    filesize = os.path.getsize(file)
    s = socket.socket()
    s.connect((host, port))
    s.send(f"{file}{separator}{filesize}".encode())
    with open(file, "rb") as f:
        while True:
            # read the bytes from the file
            bytes_read = f.read(buffersize)
            if not bytes_read:
                # file transmitting is done
                break
            # we use sendall to assure transimission in 
            # busy networks
            s.sendall(bytes_read)
    s.close()

############### MQTT section ##################

# when connecting to mqtt do this;
def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("Connection established. Code: "+str(rc))
        """ret = subprocess.run(["tdtool","-l"], capture_output = True,text = True)
        list_of_dev= ret.stdout.split("\n")
        #for now we know it's just one, later we will have to also check the id a$
        x=list_of_dev[1].split("\t")
        print(x)
        actuator_dict["onoff"] = x[len(x)-1].lower()"""
        print(actuator_dict)
        for i in sub_topic :
            print("subscribing to topic: ", i)
            client.subscribe(i)
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
    try:
        data = str(message.payload.decode("utf-8"))
        print("message received ", data)
        print("\nmessage topic=",message.topic)
        print("\nmessage qos=",message.qos)
        print("\nmessage retain flag=",message.retain)
        dict_command = json.loads(data) 
        if dict_command["cmd"] == "switch" :
            #subprocess.run(["tdtool", "--"+dict_command["onoff"], str(dict_command["id"])]) #uncomment only in raspberry
            actuator_dict["onoff"]=dict_command["onoff"]
            print("switch success")
        elif dict_command["cmd"] == "getlog" :
            print("file success")
            #send_file(file=csvfile, host=dict_command["host"], port=dict_command["port"], separator= dict_command["separator"], buffersize=int(dict_command["buffer"])) #uncomment only in raspberry
    except ValueError as error:
        print(data," ", error, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
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
client.loop_start()

# Loop that publishes message
while True:
    data_to_send = get_wattage() #dictionary
    for i in list(data_to_send.keys()) :
        actuator_dict[i]=data_to_send[i]
    
    # format sent {'id': 1, 'date': '2023-12-13T12:52:55.562Z', 'wattage': 1.2, 'onoff': 'on'}
    ret = client.publish(pub_topic, str(actuator_dict))
    print(ret)
    time.sleep(2.0)	# Set delay  """