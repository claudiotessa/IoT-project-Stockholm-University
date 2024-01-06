import csv
import json

import requests
import paho.mqtt.client as mqtt
import socket

import time
import subprocess
import multiprocessing

from actuatorDict import ActuatorDict

import pandas as pd

from sklearn.cluster import MiniBatchKMeans
from sklearn.svm import SVC
import numpy as np
from sklearn.preprocessing import StandardScaler

import joblib
from sched import scheduler

# Set MQTT broker and topic
broker = "test.mosquitto.org"  # Broker

pub_topic = ["iotProject/sensors",
             "iotProject/controls"]  # send data of sensor, send data about calculated checks and limits

sub_topic = [
    "iotProject/devices",
    "iotProject/files",
]  # control for the change in the actuator status

# logfile directory
csvfile = "detections"

# actuator dictionary for now just 1 dict, later will be a class that will index and manage multiple actuators
actuator_dict = ActuatorDict()

############### Learning section ##################

## cluster data based only off the wattage and assign to each data a cluster, then learn the data through a classifier
def find_high_low():
    mean_variance_list =[]
    #do it for every actuator
    for actuator in actuator_dict.get_all_id():
        #get last month data
        month=time.localtime().tm_mon-1
        year=time.localtime().tm_year
        if(month==0):
            month=12
            year-=1
        df = pd.read_csv(str(month)+'-'+str(year)+'detections'+str(actuator)+'.csv')

        #distinguish between a turned on appliance and a stand by appliance
        df = df.drop('id', axis=1)
        to_fit=df.drop('date', axis=1)
        kmeans = MiniBatchKMeans(n_clusters=2, n_init='auto', verbose=1).fit_predict(to_fit) #trying using something less computationally expensive
        
        #search the mean and variance of a turned on appliance to check if it's using more energy then usual
        mean_variance={"id":actuator}
        mean_variance.update(get_mean_variance(df,kmeans))
        mean_variance_list.append(mean_variance)

        #weights calculation, nl1= turned on nl2=stand by, since data is unblanced we are going to give class 1 (on) nl2/nl1 weights (# times it's off/#time it's on) 
        nl1= 0
        nl2= 0
        for i in kmeans:
            if i==1: nl1+=1
            if i==0: nl2+=1

        print(time.asctime())
        #scaling the data for easier fitting
        sc= StandardScaler()
        sc.fit(df)
        df_transformed= sc.transform(df)
        #training model 
        model= SVC(class_weight={0:1, 1:nl2/nl1}, verbose=1, gamma=10, C=0.1)
        joblib.dump(model, 'poly2.pkl')
        
        model.fit(df_transformed, kmeans)

        u=model.predict(df_transformed)
        joblib.dump(u, 'predictionsrbf.pkl')

        print(time.asctime())
        with open('output.txt', 'w') as filehandle:
            json.dump(u.tolist(), filehandle)

        df= df.assign(classes=kmeans)

        on= df_transformed[df["classes"]==1]
        regression= np.poly1d(np.polyfit(on[:,0], on[:,1], 8))
    return mean_variance_list
    
def get_mean_variance(df, kmeans):
    df= df.assign(classes=kmeans)
    on=df[df["classes"]==1]
    N=len(on)
    s=0
    for index, row in df.iterrows():
        s+=row["wattage"]
    mean=s/N

    s=0
    for index, row in df.iterrows():
        s+=pow(row["wattage"]-mean, 2)
    variance=s/N
    return {"mean":mean, "variance":variance}
    
############### Sensor section ##################

def get_wattage():
    url = "http://192.168.1.124:4000"  # change depending on who is being the simulator
    myobj = {"pi": "broker"}
    x = requests.post(url, json=myobj)
    print("writing to file: ", x.text)
    list_of_dev = json.loads(x.text)
    month = str(time.localtime().tm_mon) + "-" + str(time.localtime().tm_year)

    for y in list_of_dev:
        file_name = month + csvfile + str(y["id"]) + ".csv"
        try:
            f = open(file_name, "x")
            f.writelines(["id,date,wattage\n"])
        except Exception:
            f = open(file_name, "a")
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow([str(y["id"]), y["date"], str(y["wattage"])])
        f.close()
    return list_of_dev


############### FTP section ##################


def send_file(host, port, separator="<SEPARATOR>", size=4096, format="utf-8"):
    ADDR = (host, port)
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

        conn.send(data.encode(format))
        msg = conn.recv(size).decode(format)
        print(f"[SERVER]: {msg}")

        file.close()
        conn.close()
        print(f"[DISCONNECTED] {addr} disconnected.")


############### MQTT section ##################
def gather_actuators():
    # uncomment only in raspberry
    # ret = subprocess.run(["tdtool","-l"], capture_output = True,text = True)
    # list_of_dev= ret.stdout.split("\n")

    # comment only in raspberry
    ret = "Number of devices: 2\n1\tLighting\tON\n2\tLighting2\tOFF\n\n"
    list_of_dev = ret.split("\n")

    n_devices = int(
        list_of_dev[0].split()[-1]
    )  # this line extracts x from the string "Number of devices: x",

    for i in range(1, n_devices + 1):
        x = list_of_dev[i].split("\t")
        actuator_dict.add(id=int(x[0]), name=x[1].lower(), onoff=x[-1].lower())
    print(actuator_dict.get_act(1))
    ######### topic subscription


# when connecting to mqtt do this;
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connection established. Code: " + str(rc))

        ######## gathering actuators
        gather_actuators()

        for i in sub_topic:
            print("subscribing to topic: ", i)
            client.subscribe(i, qos=1)
    else:
        print("Connection failed. Code: " + str(rc))


def on_publish(client, userdata, mid):
    print("Published: " + str(mid))


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disonnection. Code: ", str(rc))
    else:
        print("Disconnected. Code: " + str(rc))


def on_log(client, userdata, level, buf):  # Message is in buf
    print("MQTT Log: " + str(buf))

# when getting message from a subscribed topic
# if command is to switch on or off message has to be structured like this
# {"cmd":"switch", "id": id number, "onoff": on\off status}

# if command is to program when to turn on or off message has to be structured like this
# {"cmd":"program", "id": id number, "on":ms from epoch, "off":ms from epoch} 
# if either on or off is missing then assume they want to keep it off or on

def on_message(client, userdata, message):
    try:
        data = str(message.payload.decode("utf-8"))
        print("message received ", data)
        print("\nmessage topic=", message.topic)
        print("\nmessage qos=", message.qos)
        print("\nmessage retain flag=", message.retain)
        dict_command = json.loads(data)
        if dict_command["cmd"] == "switch":
            turn_on_off(dict_command)
            print("switch success")
        if dict_command["cmd"] == "program":
            s= scheduler(time.monotonic, time.sleep)
            if dict_command["on"]!= None:
                s.enterabs(dict_command["on"], 10, turn_on_off, argument=(dict_command, ))
            if dict_command["off"]!= None:
                s.enterabs(dict_command["off"], 10, turn_on_off, argument=(dict_command, ))

    except ValueError as error:
        print(
            data,
            " ",
            error,
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        )
        return error
def turn_on_off(dict_command):
    # subprocess.run(["tdtool", "--"+dict_command["onoff"], str(dict_command["id"])]) #uncomment only in raspberry
    actuator_dict.set_act(
       id=dict_command["id"], dictio={"onoff": dict_command["onoff"]}
    )
def run_mqtt():
    # Connect functions for MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
    client.on_log = on_log
    client.on_message = on_message

    # Connect to MQTT
    print("Attempting to connect to broker " + broker)
    client.connect(
        broker
    )  # Broker address, port and keepalive (maximum period in seconds allowed between communications with the broker)
    client.loop_start()
    time.sleep(2.0)
    mean_variance_list = find_high_low()
    print(mean_variance_list)
    ret= client.publish(pub_topic[1], str(mean_variance_list))
    print(ret)
    
    # Loop that publishes message
    while True:
        time.sleep(2.0)  # Set delay  """
        data_to_send = get_wattage()  # dictionary
        p=0
        for i in data_to_send:
            ind = actuator_dict.get_act(i["id"])["index"]
            onoff= actuator_dict.get_act(i["id"])["onoff"]
            actuator_dict.set_act(ind, dictio=i)
            data_to_send[p]['onoff']=onoff
            p+=1
        # format sent [{'id': 1, 'date': milliseconds since epoch, 'wattage': 1.2, 'onoff': 'on'},...]
        print(data_to_send)
        ret = client.publish(pub_topic[0], str(data_to_send))
        print(ret)


############### starting up section ##################
if __name__ == "__main__":

    ftp_thread = multiprocessing.Process(
        target=send_file, args=("0.0.0.0", 2000), daemon=True
    )
    mqtt_thread = multiprocessing.Process(target=run_mqtt, daemon=True)

    ftp_thread.start()
    #àmqtt_thread.start()

    try:
        while 1:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("attempting to close threads.")
        ftp_thread.terminate()
        #mqtt_thread.terminate()
        print("threads successfully closed")
