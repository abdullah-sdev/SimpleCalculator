package com.example.calculator;

import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.PopupMenu;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import java.text.DecimalFormat;

public class MainActivity extends AppCompatActivity {

    private TextView tvInput, tvHistory;
    private StringBuilder currentInput = new StringBuilder();
    private String history = "";
    private boolean isResultDisplayed = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvInput = findViewById(R.id.tv_input);
        tvHistory = findViewById(R.id.tv_history);

        setNumericListeners();
        setOperatorListeners();

        findViewById(R.id.btn_clear).setOnClickListener(v -> clear());

        findViewById(R.id.btn_equals).setOnClickListener(v -> calculateResult());

        findViewById(R.id.btn_dot).setOnClickListener(v -> {
            if (currentInput.length() == 0 || currentInput.charAt(currentInput.length() - 1) == ' ') {
                appendToInput("0.");
            } else if (!hasDotInCurrentNumber()) {
                appendToInput(".");
            }
        });

        findViewById(R.id.btn_scientific).setOnClickListener(this::showScientificMenu);
    }

    private void clear() {
        currentInput.setLength(0);
        history = "";
        isResultDisplayed = false;
        updateDisplay();
    }

    private boolean hasDotInCurrentNumber() {
        int len = currentInput.length();
        for (int i = len - 1; i >= 0; i--) {
            char c = currentInput.charAt(i);
            if (c == '.') return true;
            if (c == ' ') break;
        }
        return false;
    }

    private void showScientificMenu(View v) {
        PopupMenu popup = new PopupMenu(this, v);
        popup.getMenu().add("sin");
        popup.getMenu().add("cos");
        popup.getMenu().add("tan");
        popup.getMenu().add("sqrt");
        popup.getMenu().add("log");
        popup.getMenu().add("ln");
        popup.getMenu().add("^");

        popup.setOnMenuItemClickListener(item -> {
            String func = item.getTitle().toString();
            if (func.equals("^")) {
                appendToInput(" ^ ");
            } else {
                appendToInput(func + "(");
            }
            return true;
        });
        popup.show();
    }

    private void setNumericListeners() {
        int[] numericIds = {
            R.id.btn_0, R.id.btn_1, R.id.btn_2, R.id.btn_3, R.id.btn_4,
            R.id.btn_5, R.id.btn_6, R.id.btn_7, R.id.btn_8, R.id.btn_9
        };

        View.OnClickListener listener = v -> {
            Button b = (Button) v;
            String num = b.getText().toString();
            if (isResultDisplayed) {
                currentInput.setLength(0);
                isResultDisplayed = false;
            }
            appendToInput(num);
        };

        for (int id : numericIds) {
            findViewById(id).setOnClickListener(listener);
        }
    }

    private void setOperatorListeners() {
        int[] operatorIds = {
            R.id.btn_add, R.id.btn_subtract, R.id.btn_multiply,
            R.id.btn_divide, R.id.btn_percent, R.id.btn_parenthesis
        };

        View.OnClickListener listener = v -> {
            Button b = (Button) v;
            String op = b.getText().toString();
            if (op.equals("( )")) {
                handleParenthesis();
            } else {
                if (currentInput.length() > 0 && currentInput.charAt(currentInput.length() - 1) != ' ') {
                    appendToInput(" " + op + " ");
                } else if (isResultDisplayed) {
                    currentInput.setLength(0);
                    currentInput.append(history.replace(" =", " " + op + " "));
                    isResultDisplayed = false;
                    updateDisplay();
                    return;
                }
            }
            isResultDisplayed = false;
        };

        for (int id : operatorIds) {
            findViewById(id).setOnClickListener(listener);
        }
    }

    private void handleParenthesis() {
        int openCount = 0;
        int closeCount = 0;
        for (char c : currentInput.toString().toCharArray()) {
            if (c == '(') openCount++;
            else if (c == ')') closeCount++;
        }

        if (openCount == closeCount || currentInput.length() == 0 ||
                currentInput.charAt(currentInput.length() - 1) == ' ' ||
                currentInput.charAt(currentInput.length() - 1) == '(') {
            appendToInput("(");
        } else {
            appendToInput(")");
        }
    }

    private void appendToInput(String str) {
        currentInput.append(str);
        updateDisplay();
    }

    private void calculateResult() {
        if (currentInput.length() == 0) return;

        String expr = currentInput.toString();
        while (expr.endsWith(" ")) {
            expr = expr.substring(0, expr.length() - 1);
        }
        while (expr.startsWith(" ")) {
            expr = expr.substring(1);
        }

        if (expr.isEmpty() || expr.equals("(")) return;

        int openCount = 0, closeCount = 0;
        for (char c : expr.toCharArray()) {
            if (c == '(') openCount++;
            else if (c == ')') closeCount++;
        }
        while (openCount > closeCount) {
            expr += ")";
            currentInput.append(")");
            closeCount++;
        }

        try {
            double result = CalculatorLogic.evaluate(expr);
            history = currentInput.toString() + " =";
            currentInput.setLength(0);
            currentInput.append(formatResult(result));
            isResultDisplayed = true;
            updateDisplay();
        } catch (Exception e) {
            tvInput.setText("Error");
        }
    }

    private String formatResult(double result) {
        if (result == (long) result && !Double.isInfinite(result)) {
            return String.format("%d", (long) result);
        } else {
            return new DecimalFormat("#.####").format(result);
        }
    }

    private void updateDisplay() {
        String display = currentInput.toString();
        tvInput.setText(display.isEmpty() ? "0" : display);
        tvHistory.setText(history);
    }
}