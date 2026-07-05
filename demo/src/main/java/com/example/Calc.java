package com.example;

public class Calc {
    public int add(int a, int b) {
        return a + b;
    }

    public int sub(int a, int b) {
        return a - b;
    }

    
    public int boxed() {
        Integer x = new Integer(3); // deliberate deprecation warning
        return x;
    }
}
