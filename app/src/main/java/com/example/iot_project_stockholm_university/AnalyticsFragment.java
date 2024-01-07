package com.example.iot_project_stockholm_university;

import android.os.AsyncTask;
import android.os.Bundle;

import androidx.fragment.app.Fragment;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/**
 * A simple {@link Fragment} subclass.
 * Use the {@link AnalyticsFragment#newInstance} factory method to
 * create an instance of this fragment.
 */
public class AnalyticsFragment extends Fragment {

    // TODO: Rename parameter arguments, choose names that match
    // the fragment initialization parameters, e.g. ARG_ITEM_NUMBER
    private static final String ARG_PARAM1 = "param1";
    private static final String ARG_PARAM2 = "param2";

    // TODO: Rename and change types of parameters
    private String mParam1;
    private String mParam2;

    LinearLayout linearLayout;

    public AnalyticsFragment() {
        // Required empty public constructor
    }

    /**
     * Use this factory method to create a new instance of
     * this fragment using the provided parameters.
     *
     * @param param1 Parameter 1.
     * @param param2 Parameter 2.
     * @return A new instance of fragment AnalyticsFragment.
     */
    // TODO: Rename and change types and number of parameters
    public static AnalyticsFragment newInstance(String param1, String param2) {
        AnalyticsFragment fragment = new AnalyticsFragment();
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
        View rootView = inflater.inflate(R.layout.fragment_analytics, container, false);
        linearLayout = (LinearLayout) rootView.findViewById(R.id.linearLayoutRecommendations);

        new RequestAnalytics().execute("12-2023detections1.csv", "192.168.1.124", "2000");
        return rootView;
    }

    public void renderRecommendations(ArrayList<String> recommendations) {
        for (String recommendation : recommendations) {
            View view = LayoutInflater.from(getContext()).inflate(R.layout.recommendation_card, null);
            linearLayout.addView(view);

            TextView recommendationText = view.findViewById(R.id.recommendationText);
            recommendationText.setText(recommendation);
        }
    }
}

class RequestAnalytics extends AsyncTask<String, Void, String> {
    String host;
    Integer port;
    @Override
    protected String doInBackground(String... args) {
        try{
            host = args[1];
            port = Integer.parseInt(args[2]);
            String msg = args[0];

            Socket socket = new Socket(host, port);

            DataOutputStream dataOutputStream = new DataOutputStream(socket.getOutputStream());
            DataInputStream dataInputStream = new DataInputStream(socket.getInputStream());

            // send msg
            dataOutputStream.write(msg.getBytes("UTF-8"));
            dataOutputStream.flush();

            // read msg
            String response = String.valueOf(dataInputStream.read());

            dataOutputStream.write("file received".getBytes("UTF-8"));
            dataOutputStream.flush();

            socket.close();

            return response;

        }catch (Exception e){
            e.printStackTrace();
            return "error tcp";
        }
    }

    @Override
    protected void onPostExecute(String response){
        //after execution render consumption chart
        System.out.println("Response: " + response);
    }
}