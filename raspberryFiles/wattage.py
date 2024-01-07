import csv
import json
from datetime import datetime

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

pub_topic = [
    "iotProject/sensors",
    "iotProject/controls",
]  # send data of sensor, send data about calculated checks and limits

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
    mean_variance_list = []
    # do it for every actuator
    for actuator in actuator_dict.get_all_id():
        # get last month data
        month = time.localtime().tm_mon - 1
        year = time.localtime().tm_year
        if month == 0:
            month = 12
            year -= 1
        df = pd.read_csv(
            str(month) + "-" + str(year) + "detections" + str(actuator) + ".csv"
        )

        first_of_month = df.iloc[0]["date"]
        df["date"] = (
            df["date"]
            - (86400000 * ((df["date"] - first_of_month) // 86400000))
            - first_of_month
        )
        # distinguish between a turned on appliance and a stand by appliance
        df = df.drop("id", axis=1)
        to_fit = df.drop("date", axis=1)
        kmeans = MiniBatchKMeans(n_clusters=2, n_init="auto", verbose=1).fit_predict(
            to_fit
        )  # trying using something less computationally expensive
        # {"id":id, }

        df = df.assign(classes=kmeans)
        on = df[df["classes"] == 1].to_numpy()

        # search the mean and calculate an upperbound of wattage that is used as a general limit to find if the aplliance is consuming more then usual
        # meaning that it is probably broken and need repairing

        suggestions = {"id": actuator}

        perc = int(len(on) * 0.1)  # watch just the top 10% of the data
        sorted_wattage = on[on[:, 1].argsort()]
        maximum = sorted_wattage[1 - perc :, 1]
        print(maximum)
        suggestions.update(
            {
                "mean": np.mean(on[:, 1]),
                "max": np.mean(maximum) + np.sqrt(np.var(on[:, 1])),
            }
        )
        # watching the first and last 10% of the data we can find a decent point of start that should not too influenced by outliers
        sorted_time = on[on[:, 0].argsort()]
        first = sorted_time[:perc, 0]
        last = sorted_time[1 - perc :, 0]
        # add 10 minutes to start and end time to give a bit of leaway
        start = np.mean(first) - 10 * 1000 * 60
        end = np.mean(last) + 10 * 1000 * 60

        suggestions.update({"start": start, "end": end})
        mean_variance_list.append(suggestions)
    return mean_variance_list


############### Sensor section ##################


# gathers data from the simulator, to change the wattage
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
        try:
            file = open(filename, "r")
            data = file.read()
            rows = data.split("\n")[1:-1]
            data_to_send = {}
            for row in rows:
                timestamp, wattage = row.split(",")[1:]
                timestamp = int(timestamp[0:-3])

                wattage = float(wattage)

                day = datetime.fromtimestamp(timestamp).day
                hour = datetime.fromtimestamp(timestamp).hour

                # format: {day : {hour: {value: wattage_sum, count: detections_count}}}
                if day in data_to_send:
                    if hour in data_to_send:
                        data_to_send[day][hour]["value"] += wattage
                        data_to_send[day][hour]["count"] += 1
                    else:
                        data_to_send[day][hour] = {"value": wattage, "count": 1}
                else:
                    data_to_send[day] = {hour: {"value": wattage, "count": 1}}

            # transform in format: {day: total_consumption}
            for day in data_to_send:
                day_consumption = 0
                for hour in data_to_send[day]:
                    day_consumption += (
                        data_to_send[day][hour]["value"]
                        / data_to_send[day][hour]["count"]
                    )
                data_to_send[day] = day_consumption

            conn.send(json.dumps(data_to_send).encode(format))
            msg = conn.recv(size).decode(format)
            print(f"[SERVER]: {msg}")
        except:
            conn.send("Filename not found.".encode(format))
        file.close()
        conn.close()
        print(f"[DISCONNECTED] {addr} disconnected.")


############### MQTT section ##################
def gather_actuators():
    # checks how many actuators are connected to the raspberrypy
    # uncomment only in raspberry
    # ret = subprocess.run(["tdtool","-l"], capture_output = True,text = True)
    # list_of_dev= ret.stdout.split("\n")

    # comment only in raspberry
    ret = "Number of devices: 2\n1\tLighting\tON\n2\tLighting2\tON\n\n"
    list_of_dev = ret.split("\n")

    # this line extracts x from the string "Number of devices: x",
    n_devices = int(list_of_dev[0].split()[-1])

    for i in range(1, n_devices + 1):
        x = list_of_dev[i].split("\t")
        actuator_dict.add(id=int(x[0]), name=x[1].lower(), onoff=x[-1].lower())
    print(actuator_dict.get_act(1))


# when connecting to mqtt do this;
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connection established. Code: " + str(rc))

        ######## gathering actuators
        gather_actuators()

        ######### topic subscription
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
            s = scheduler(time.monotonic, time.sleep)
            if dict_command["on"] != None:
                s.enterabs(
                    dict_command["on"], 10, turn_on_off, argument=(dict_command,)
                )
            if dict_command["off"] != None:
                s.enterabs(
                    dict_command["off"], 10, turn_on_off, argument=(dict_command,)
                )

    except ValueError as error:
        print(
            data,
            " ",
            error,
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        )
        return error


def turn_on_off(dict_command):
    # sends a shell command to the raspberry to activate the actuator
    # uncomment only in raspberrypi
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

    # find the suggestions based on last month data
    suggestions = find_high_low()
    print(suggestions)
    ret = client.publish(pub_topic[1], str(suggestions))
    print(ret)

    # Loop that publishes message
    while True:
        time.sleep(2.0)  # Set delay
        data_to_send = get_wattage()  # dictionary
        p = 0
        for i in data_to_send:
            # actuator dict is an object with a list of dictionaries containing all the data of a actuator
            # here i update all the data of every actuator after i gather it through get_wattage()
            ind = actuator_dict.get_act(i["id"])["index"]
            onoff = actuator_dict.get_act(i["id"])["onoff"]
            actuator_dict.set_act(ind, dictio=i)
            data_to_send[p]["onoff"] = onoff
            p += 1
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
    mqtt_thread.start()

    try:
        while 1:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("attempting to close threads.")
        ftp_thread.terminate()
        mqtt_thread.terminate()
        print("threads successfully closed")
