package com.example.calculator;

import org.junit.Test;
import static org.junit.Assert.*;

public class CalculatorTest {
    @Test
    public void testAddition() {
        assertEquals(5.0, CalculatorLogic.evaluate("2 + 3"), 0.001);
    }

    @Test
    public void testMultiplication() {
        assertEquals(15.0, CalculatorLogic.evaluate("3 * 5"), 0.001);
    }

    @Test
    public void testScientific() {
        // sin(90) = 1.0
        assertEquals(1.0, CalculatorLogic.evaluate("sin(90)"), 0.001);
        // sqrt(16) = 4.0
        assertEquals(4.0, CalculatorLogic.evaluate("sqrt(16)"), 0.001);
    }

    @Test
    public void testPrecedence() {
        assertEquals(17.0, CalculatorLogic.evaluate("2 + 3 * 5"), 0.001);
    }
}
