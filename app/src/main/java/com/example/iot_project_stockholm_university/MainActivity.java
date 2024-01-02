package com.example.iot_project_stockholm_university;

import androidx.appcompat.app.AppCompatActivity;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentManager;
import androidx.fragment.app.FragmentTransaction;

import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.CompoundButton;
import android.widget.LinearLayout;
import android.widget.Switch;
import android.widget.TextView;

import com.example.iot_project_stockholm_university.databinding.ActivityMainBinding;

import org.eclipse.paho.android.service.MqttAndroidClient;
import org.eclipse.paho.client.mqttv3.IMqttActionListener;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.IMqttToken;
import org.eclipse.paho.client.mqttv3.MqttCallbackExtended;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.json.*;

import java.util.ArrayList;

public class MainActivity extends AppCompatActivity {

    ActivityMainBinding binding; // used for navbar

    private MqttAndroidClient client;
    private static final String SERVER_URI = "tcp://test.mosquitto.org:1883";
    private static final String TAG = "MainActivity";

    private static final String SENSORS_TOPIC = "iotProject/sensors";
    private static final String DEVICES_TOPIC = "iotProject/devices";
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());
        replaceFragment(new HomeFragment(), "home");
        readRealTimeDevicesData("[{id:1, timestamp:1704130156, wattage: 1.2}, {id:2, timestamp:1704130157, wattage: 1.4}]");

        connect();

        // callback for MQTT
        client.setCallback(new MqttCallbackExtended() {
            @Override
            public void connectComplete(boolean reconnect, String serverURI) {
                if (reconnect) {
                    System.out.println("Reconnected to : " + serverURI);
                    // Re-subscribe as we lost it due to new session
                    subscribe(SENSORS_TOPIC);
                } else {
                    System.out.println("Connected to: " + serverURI);
                    subscribe(SENSORS_TOPIC);
                }
            }
            @Override
            public void connectionLost(Throwable cause) {
                System.out.println("The Connection was lost.");
            }
            @Override
            public void messageArrived(String topic, MqttMessage message) throws Exception {
                String newMessage = new String(message.getPayload());
                System.out.println("Incoming message: " + newMessage);

                readRealTimeDevicesData(newMessage);
            }
            @Override
            public void deliveryComplete(IMqttDeliveryToken token) {}
        });

        // Attempt to invoke virtual method 'void org.eclipse.paho.android.service.MqttService.subscribe(java.lang.String, java.lang.String, int, java.lang.String, java.lang.String)' on a null object reference
        //subscribe(SENSORS_TOPIC);

        // event listener for when the user clicks on a navbar button
        // chooses the correct fragment to display
        binding.bottomNavigationView.setOnItemSelectedListener(item -> {
            int itemId = item.getItemId();
            if(itemId == R.id.home){
                replaceFragment(new HomeFragment(), "home");

            } else if(itemId == R.id.analytics){
                replaceFragment(new AnalyticsFragment(), "analytics");
            }

            return true;
        });
    }

    // connect to MQTT server
    private void connect(){
        String clientId = MqttClient.generateClientId();
        client = new MqttAndroidClient(this.getApplicationContext(), SERVER_URI, clientId);

        try {
            IMqttToken token = client.connect();

            token.setActionCallback(new IMqttActionListener() {
                @Override
                public void onSuccess(IMqttToken asyncActionToken) {
                    // We are connected
                    Log.d(TAG, "onSuccess");
                    System.out.println(TAG + " Success. Connected to " + SERVER_URI);
                }
                @Override
                public void onFailure(IMqttToken asyncActionToken, Throwable exception)
                {
                    // Something went wrong e.g. connection timeout or firewall problems
                    Log.d(TAG, "onFailure");
                    System.out.println(TAG + " Oh no! Failed to connect to " + SERVER_URI);
                }
            });
        }
        catch (MqttException e) {
            e.printStackTrace();
        }
    }

    // subscribe to a specific topic
    private void subscribe(String topicToSubscribe) {
        final String topic = topicToSubscribe;
        int qos = 1;
        try {
            IMqttToken subToken = client.subscribe(topic, qos);
            subToken.setActionCallback(new IMqttActionListener() {
                @Override
                public void onSuccess(IMqttToken asyncActionToken) {
                    System.out.println("Subscription successful to topic: " + topic);
                }
                @Override
                public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                    System.out.println("Failed to subscribe to topic: " + topic);
                    // The subscription could not be performed, maybe the user was not
                    // authorized to subscribe on the specified topic e.g. using wildcards
                }
            });
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    // when called, replaces the passed fragment (active page)
    private void replaceFragment(Fragment fragment, String tag){
        FragmentManager fragmentManager = getSupportFragmentManager();
        FragmentTransaction fragmentTransaction = fragmentManager.beginTransaction();
        fragmentTransaction.replace(R.id.frame_layout, fragment, tag);
        fragmentTransaction.commit();

        System.out.println(fragmentManager.getFragments().size());
    }

    private void readRealTimeDevicesData(String data){
        try {
            // read every device into an array;
            JSONArray devices;
            ArrayList<RealTimeDeviceData> realTimeDevicesData = new ArrayList<>();
            devices = new JSONArray(data);
            LinearLayout layout = findViewById(R.id.linearLayoutScrollView);

            for(int i = 0; i < devices.length(); i++){
                //read json into java object
                realTimeDevicesData.add(new RealTimeDeviceData(
                    Integer.parseInt(devices.getJSONObject(i).getString("id")),
                    Integer.parseInt(devices.getJSONObject(i).getString("timestamp")),
                    Double.parseDouble(devices.getJSONObject(i).getString("wattage"))
                ));

                View view = getLayoutInflater().inflate(R.layout.device_card, null);
                TextView deviceName = view.findViewById(R.id.deviceName);
                TextView consumption = view.findViewById(R.id.textConsumption);
                Switch switchDevice = view.findViewById(R.id.switchDevice);

                switchDevice.setOnCheckedChangeListener((buttonView, isChecked) -> {
                    System.out.println(isChecked);
                });
            }
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }


}