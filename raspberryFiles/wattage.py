import requests
import csv
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import socket
import subprocess
import multiprocessing
from actuatorDict import ActuatorDict

# Set MQTT broker and topic
broker = "test.mosquitto.org"	# Broker 

pub_topic = "iotProject/sensors" #send data of sensor
sub_topic = ["iotProject/devices", "iotProject/files"] #control for the change in the actuator status

# logfile directory
csvfile = 'detections.csv'

#actuator dictionary for now just 1 dict, later will be a class that will index and manage multiple actuators
actuator_dict = ActuatorDict()

############### Sensor section ##################

def get_wattage():
    url = "http://192.168.255.250:4000" #change depending on who is being the simulator
    myobj = {'pi': "broker"}
    x = requests.post(url, json = myobj)
    print("writing to file: ", x.text)
    list_of_dev = json.loads(x.text)
    for y in list_of_dev :
        f = open(csvfile+str(y["id"]), 'a')
        writer = csv.writer(f, lineterminator = '\n')
        writer.writerow([str(y["id"]), y["date"], str(y["wattage"])])
        f.close()
    return list_of_dev

############### FTP section ##################

def send_file(host, port, separator="<SEPARATOR>", size=4096, format = "utf-8") :
    ADDR=(host, port)
    print("listnening for file requests")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 
    server.bind(ADDR)
    server.listen()

    print("[LISTENING] Server is listening.")
 
    while True:
        conn, addr = server.accept()
        print(f"[NEW CONNECTION] {addr} connected.")

        filename = conn.recv(size).decode(format)
        print("[RECV] Receiving the filename.")
        file = open(filename, "r")
        data = file.read()
        conn.send("Filename received.".encode(format))

        server.send(data.encode(format))
        msg = server.recv(size).decode(format)
        print(f"[SERVER]: {msg}")

        file.close()
        conn.close()
        print(f"[DISCONNECTED] {addr} disconnected.")

############### MQTT section ##################

# when connecting to mqtt do this;
def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("Connection established. Code: "+str(rc))
        
        ######## gathering actuators

        #uncomment only in raspberry
        #ret = subprocess.run(["tdtool","-l"], capture_output = True,text = True)
        #list_of_dev= ret.stdout.split("\n") 

        #comment only in raspberry
        ret= "Number of devices: 2\n1\tLighting\tON\n2\tLighting2\tON\n\n"
        list_of_dev=ret.split("\n")
        
        n_devices = int(list_of_dev[0].split()[-1]) #this line extracts x from the string "Number of devices: x", 

        for i in range(1,n_devices+1) :
            x=list_of_dev[i].split("\t")
            actuator_dict.add(id=int(x[0]), name=x[1].lower(),onoff=x[-1].lower())
        print(actuator_dict.get_act(1))
        ######### topic subscription
        
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
            x= actuator_dict.get_act(dict_command["id"])
            actuator_dict.set_act(id=x[id], noff=dict_command["onoff"])
            print("switch success")

    except ValueError as error:
        print(data," ", error, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        return error

def run_mqtt() :
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
        time.sleep(2.0) # Set delay  """
        data_to_send = get_wattage() #dictionary
        for i in data_to_send :
            ind= actuator_dict.get_act(i["id"])["index"]
            actuator_dict.set_act(ind, dictio=i)
        # format sent [{'id': 1, 'date': '2023-12-13T12:52:55.562Z', 'wattage': 1.2, 'onoff': 'on'},...]
        
        ret = client.publish(pub_topic, str(data_to_send))
        print(ret)
        	

############### starting up section ##################
if __name__ == '__main__':
    ftp_thread = multiprocessing.Process(target=send_file, args=("192.168.255.250",2000), daemon=True)
    mqtt_thread = multiprocessing.Process(target=run_mqtt, daemon=True)



    #ftp_thread.start()
    mqtt_thread.start()

    try:
        while 1:
            time.sleep(.1)
    except KeyboardInterrupt:
        print( "attempting to close threads.")
        #ftp_thread.terminate()
        mqtt_thread.terminate()
        print("threads successfully closed")