package com.example.iot_project_stockholm_university;

import android.app.AlertDialog;
import android.app.Dialog;
import android.content.Context;
import android.content.DialogInterface;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.EditText;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatDialogFragment;

public class BudgetDialog extends AppCompatDialogFragment {
    private EditText budgetAmount;
    @Override
    public Dialog onCreateDialog(Bundle savedInstanceState) {
        AlertDialog.Builder builder = new AlertDialog.Builder(getActivity());
        LayoutInflater layoutInflater = getActivity().getLayoutInflater();
        View view = layoutInflater.inflate(R.layout.budget_dialog, null);
        builder.setView(view)
                .setTitle("Set your monthly budget!")
                .setNegativeButton("Cancel", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) { }
                })
                .setPositiveButton("Ok", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        String budget = budgetAmount.getText().toString();
                        AnalyticsFragment analyticsFragment = (AnalyticsFragment) getFragmentManager().findFragmentByTag("analytics");
                        analyticsFragment.applyBudget(budget);
                    }
                });
        budgetAmount = view.findViewById(R.id.budgetAmount);
        return builder.create();
    }
}
