package com.example.iot_project_stockholm_university;

import android.os.AsyncTask;
import android.os.Bundle;

import androidx.fragment.app.Fragment;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.github.mikephil.charting.charts.LineChart;
import com.github.mikephil.charting.data.Entry;
import com.github.mikephil.charting.data.LineData;
import com.github.mikephil.charting.data.LineDataSet;

import org.json.JSONObject;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;

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
    public static LineChart chart;
    public static int budget = 0;
    Button budgetButton;
    TextView budgetText;
    public static HashMap<Integer, Double> totalDailyConsumption;


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
        chart = (LineChart) rootView.findViewById(R.id.chart);
        chart.setDrawGridBackground(false);
        chart.setDrawBorders(false);


        budgetButton = (Button) rootView.findViewById(R.id.budgetButton);
        budgetText = (TextView) rootView.findViewById(R.id.budgetText);

        budgetButton.setOnClickListener((View view) -> {
            BudgetDialog budgetDialog = new BudgetDialog();
            budgetDialog.show(getActivity().getSupportFragmentManager(), "budget dialog");
        });
        applyBudget(AnalyticsFragment.budget + "");
        System.out.println("Executing request...");
        new RequestAnalytics().execute("1", "2");
        return rootView;
    }

    public void renderRecommendations(ArrayList<String> recommendations) {
        for (String recommendation : recommendations) {
            View view = LayoutInflater.from(getContext()).inflate(R.layout.recommendation_card, null);
            linearLayout.addView(view);

            TextView recommendationText = view.findViewById(R.id.recommendationText);
            Button deleteButton = view.findViewById(R.id.deleteButton);
            deleteButton.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    ((ViewManager)view.getParent()).removeView(view);
                }
            });
            recommendationText.setText(recommendation);
        }
    }

    public void applyBudget(String budget) {
        this.budget = Integer.parseInt(budget);
        budgetText.setText("Budget: " + budget + " w/mo");
        checkBudget();
    }

    public void checkBudget() {
        if (budget == 0) {
            System.out.println("Budget not set");
            return;
        }
        int detectedDays = totalDailyConsumption.size();
        double dailyAverage = 0;
        for (Integer key : totalDailyConsumption.keySet()) {
            dailyAverage += totalDailyConsumption.get(key);
            System.out.println(key + ": " + totalDailyConsumption.get(key));
        }
        dailyAverage = (double) dailyAverage / detectedDays;


        System.out.println("dailyavg:" + dailyAverage);
        String str = "";
        if (dailyAverage * 30 > budget) {
            int missingDays = (int) ((budget - dailyAverage * detectedDays) / dailyAverage);
            if (missingDays > 0) {
                str = "At this pace, you will go overbudget in "
                        + missingDays
                        + " days (before the end of the month).";
            } else {
                str = "Oh no! You are already overbudget :(";
            }
        } else {
            str = "At this pace, you will stay within your budget for this month! :)";
        }
        renderRecommendations(new ArrayList<>(Arrays.asList(str)));

    }
}

class RequestAnalytics extends AsyncTask<String, Void, ArrayList<String>> {
    private static final String HOST = "192.168.1.124";
    private static final int PORT = 2000;

    @Override
    protected ArrayList<String> doInBackground(String... args) {
        try {
            ArrayList<String> responses = new ArrayList<>();

            System.out.println("Starting request of files");
            for (String id : args) {
                Socket socket = new Socket(HOST, PORT);

                DataOutputStream dataOutputStream = new DataOutputStream(socket.getOutputStream());
                DataInputStream dataInputStream = new DataInputStream(socket.getInputStream());
                String fileName = LocalDate.now().getMonthValue()
                        + "-" + LocalDate.now().getYear() + "detections" + id + ".csv";
                // send msg
                System.out.println("Sending: " + fileName);
                dataOutputStream.write(fileName.getBytes("UTF-8"));
                dataOutputStream.flush();

                // read msg
                byte[] b = new byte[4096];
                int count = dataInputStream.read(b);
                String resp = new String(b, StandardCharsets.UTF_8);
                ;
                System.out.println("Received: " + resp);
                responses.add(id);
                responses.add(resp);

                dataOutputStream.write("file received".getBytes("UTF-8"));
                dataOutputStream.flush();
                dataInputStream.close();

                dataInputStream.close();
                socket.close();
            }


            return responses;

        } catch (Exception e) {
            e.printStackTrace();
            return new ArrayList<String>(Arrays.asList("-1"));
        }
    }

    @Override
    protected void onPostExecute(ArrayList<String> result) {
        //after execution render consumption chart
        if (result.get(0).equals("-1")) {
            System.out.println("result -1");
            return;
        }
        ;

        try {
            LineData lineData = new LineData();
            HashMap<Integer, Double> totalDailyConsumption = new HashMap<>();
            for (int i = 0; i < result.size() - 1; i += 2) {
                JSONObject jsonObject = new JSONObject(result.get(i + 1));
                Iterator<String> keys = jsonObject.keys();
                List<Entry> entries = new ArrayList<Entry>();
                while (keys.hasNext()) {
                    String key = keys.next();
                    // turn data into Entry objects to be read from the chart
                    entries.add(new Entry(Integer.parseInt(key), (float) jsonObject.getDouble(key)));
                    if (totalDailyConsumption.containsKey(Integer.parseInt(key))) {
                        totalDailyConsumption.put(
                                Integer.parseInt(key),
                                totalDailyConsumption.get(Integer.parseInt(key)) + jsonObject.getDouble(key)
                        );
                    } else {
                        totalDailyConsumption.put(Integer.parseInt(key), jsonObject.getDouble(key));
                    }
                }
                LineDataSet dataSet = new LineDataSet(entries, result.get(i)); // add entries to dataset
                lineData.addDataSet(dataSet);
            }
            AnalyticsFragment.chart.setData(lineData);
            AnalyticsFragment.chart.invalidate();
            AnalyticsFragment.totalDailyConsumption = totalDailyConsumption;
        } catch (Exception e) {
            e.printStackTrace();
            System.out.println("result format error");
        }
    }
}