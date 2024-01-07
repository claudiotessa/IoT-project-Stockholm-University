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
import java.util.List;

public class MainActivity extends AppCompatActivity {

    ActivityMainBinding binding; // used for navbar

    private MqttAndroidClient client;
    private static final String SERVER_URI = "tcp://test.mosquitto.org:1883";
    private static final String TAG = "MainActivity";

    private static final String SENSORS_TOPIC = "iotProject/sensors";
    public static final String DEVICES_TOPIC = "iotProject/devices";
    private FragmentManager fragmentManager;


    String prova = "[{id:1, timestamp:1704130156, wattage: 1.2}, {id:2, timestamp:1704130157, wattage: 1.4}]";
    String recc = "[{recommendation: 'At this pace, you will go overbudget in 12 days (before the end of the moth'},{recommendation: 'Device id:1 had an unusual spike around 5pm today'}]";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());
        fragmentManager = getSupportFragmentManager();
        replaceFragment(new HomeFragment(), "home");


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

                if(topic == SENSORS_TOPIC){
                    readRealTimeDevicesData(newMessage);
                }
            }

            @Override
            public void deliveryComplete(IMqttDeliveryToken token) {
            }
        });

        // Attempt to invoke virtual method 'void org.eclipse.paho.android.service.MqttService.subscribe(java.lang.String, java.lang.String, int, java.lang.String, java.lang.String)' on a null object reference
        //subscribe(SENSORS_TOPIC);

        // event listener for when the user clicks on a navbar button
        // chooses the correct fragment to display
        binding.bottomNavigationView.setOnItemSelectedListener(item -> {
            int itemId = item.getItemId();
            if (itemId == R.id.home) {
                replaceFragment(new HomeFragment(), "home");
                // test rendering real time data;
                readRealTimeDevicesData(prova);
            } else if (itemId == R.id.analytics) {
                replaceFragment(new AnalyticsFragment(), "analytics");
                //test rendering reccomendations
                readRecommendations(recc);
            }

            return true;
        });
    }

    // connect to MQTT server
    private void connect() {
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
                    subscribe(SENSORS_TOPIC);
                }

                @Override
                public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                    // Something went wrong e.g. connection timeout or firewall problems
                    Log.d(TAG, "onFailure");
                    System.out.println(TAG + " Oh no! Failed to connect to " + SERVER_URI);
                }
            });
        } catch (MqttException e) {
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

    // send message to MQTT broker
    public void publish(String topic, String message) throws MqttException {
        try {
            client.publish(topic, new MqttMessage(message.getBytes()));
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    // when called, replaces the passed fragment (active page)
    private void replaceFragment(Fragment fragment, String tag) {
        FragmentTransaction fragmentTransaction = fragmentManager.beginTransaction();
        fragmentTransaction.replace(R.id.frame_layout, fragment, tag);
        fragmentTransaction.commit();

        // make sure the fragment is completely replaced before moving on
        fragmentManager.executePendingTransactions();

    }

    private void readRealTimeDevicesData(String data) {
        try {
            // read every device into an array;
            ArrayList<RealTimeDeviceData> realTimeDevicesData = new ArrayList<>();
            JSONArray jsonArray = new JSONArray(data);
            for (int i = 0; i < jsonArray.length(); i++) {
                //read json into java object
                realTimeDevicesData.add(new RealTimeDeviceData(
                        Integer.parseInt(jsonArray.getJSONObject(i).getString("id")),
                        Integer.parseInt(jsonArray.getJSONObject(i).getString("timestamp")),
                        Double.parseDouble(jsonArray.getJSONObject(i).getString("wattage"))
                ));
            }
            HomeFragment homeFragment = (HomeFragment) fragmentManager.findFragmentByTag("home");
            if (homeFragment != null) {
                homeFragment.renderDevicesCards(realTimeDevicesData, this);
            } else {
                System.out.println("Cannot display real time data. Home Fragment not loaded!");
            }
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }
    }

    public void readRecommendations(String data) {
        try {
            ArrayList<String> recommendations = new ArrayList<>();
            JSONArray jsonArray = new JSONArray(data);
            for (int i = 0; i < jsonArray.length(); i++) {
                recommendations.add(
                        jsonArray.getJSONObject(i).getString("recommendation")
                );
            }

            AnalyticsFragment analyticsFragment = (AnalyticsFragment) fragmentManager.findFragmentByTag("analytics");
            if (analyticsFragment != null) {
                analyticsFragment.renderRecommendations(recommendations);
            } else {
                System.out.println("Cannot display recommendations yet. Analytics Fragment not loaded!");
            }
        } catch (JSONException e) {
            e.printStackTrace();
        }

    }

}