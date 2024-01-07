package com.example.iot_project_stockholm_university;

import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;

import androidx.cardview.widget.CardView;
import androidx.core.content.res.ResourcesCompat;
import androidx.fragment.app.Fragment;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.Switch;
import android.widget.TextView;

import org.eclipse.paho.client.mqttv3.MqttException;

import java.util.ArrayList;
import java.util.Dictionary;

/**
 * A simple {@link Fragment} subclass.
 * Use the {@link HomeFragment#newInstance} factory method to
 * create an instance of this fragment.
 */
public class HomeFragment extends Fragment {

    // TODO: Rename parameter arguments, choose names that match
    // the fragment initialization parameters, e.g. ARG_ITEM_NUMBER
    private static final String ARG_PARAM1 = "param1";
    private static final String ARG_PARAM2 = "param2";

    // TODO: Rename and change types of parameters
    private String mParam1;
    private String mParam2;

    LinearLayout linearLayout;
    public HomeFragment() {
        // Required empty public constructor
    }

    /**
     * Use this factory method to create a new instance of
     * this fragment using the provided parameters.
     *
     * @param param1 Parameter 1.
     * @param param2 Parameter 2.
     * @return A new instance of fragment HomeFragment.
     */
    // TODO: Rename and change types and number of parameters
    public static HomeFragment newInstance(String param1, String param2) {
        HomeFragment fragment = new HomeFragment();
        Bundle args = new Bundle();
        args.putString(ARG_PARAM1, param1);
        args.putString(ARG_PARAM2, param2);
        fragment.setArguments(args);
        return fragment;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (getArguments() != null) {
            mParam1 = getArguments().getString(ARG_PARAM1);
            mParam2 = getArguments().getString(ARG_PARAM2);
        }
    }


    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        View rootView =  inflater.inflate(R.layout.fragment_home, container, false);
        linearLayout = (LinearLayout) rootView.findViewById(R.id.linearLayoutHomeFragment);
        return rootView;
    }


    // renders the cards showing devices data in real time
    public void renderDevicesCards(ArrayList<RealTimeDeviceData> realTimeDevicesData, MainActivity mainActivity){
        double totalConsumption = 0;
        for (RealTimeDeviceData d : realTimeDevicesData) {
            View view = LayoutInflater.from(getContext()).inflate(R.layout.device_card, null);
            linearLayout.addView(view);
            TextView deviceName = view.findViewById(R.id.deviceName);
            TextView textConsumption = view.findViewById(R.id.textConsumption);
            Switch switchDevice = view.findViewById(R.id.switchDevice);
            deviceName.setText(Integer.toString(d.id));
            textConsumption.setText(d.wattage + " W/h");
            switchDevice.setOnCheckedChangeListener((listener, isChecked) -> {
                if(isChecked){
                    System.out.println(d.id + " was activated");
                    try{
                        mainActivity.publish(mainActivity.DEVICES_TOPIC, "{\"cmd\":\"switch\", \"id\": " + d. id + ", \"onoff\": \"on\"}");
                    }catch (MqttException e){
                        e.printStackTrace();
                    }
                }else {
                    System.out.println(d.id + " was deactivated");
                    try{
                        mainActivity.publish(mainActivity.DEVICES_TOPIC, "{\"cmd\":\"switch\", \"id\": " + d. id + ", \"onoff\": \"off\"}");
                    }catch (MqttException e){
                        e.printStackTrace();
                    }
                }
            });
            totalConsumption += d.wattage;
        }
        TextView totalConsumptionText = getView().findViewById(R.id.totalConsumption);
        // rounds to 2 decimal places
        totalConsumptionText.setText("Total: " + String.format("%.2f", totalConsumption) + " W/h");
    }


}