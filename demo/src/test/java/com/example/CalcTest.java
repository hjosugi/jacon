package com.example;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class CalcTest {
    @Test
    void addWorks() {
        assertEquals(3, new Calc().add(1, 2));
    }

    @Test
    void subWorks() {
        // Change 3 to 99 and save: jbacon rebuilds and shows the failure.
        assertEquals(3, new Calc().sub(5, 2));
    }
}
