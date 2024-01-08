package com.example.iot_project_stockholm_university;

public class RealTimeDeviceData {
    int id;
    int timestamp;
    double wattage;
    boolean isOn;

    public RealTimeDeviceData(int id, int timestamp, double wattage, String status){
        this.id = id;
        this.timestamp = timestamp;
        this.wattage = wattage;
        if(status.equals("on")){
            isOn = true;
        }else if (status.equals("off")){
            isOn = false;
        } else{
            isOn = false;
            System.out.println("Error status not correct");
        }
    }
}

