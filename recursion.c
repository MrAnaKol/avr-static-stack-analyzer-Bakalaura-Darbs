/*
 * AVR recursion examples for specific pattern types
 * Goal: test script pattern recognition
 * MCU: atmega328p
 */

#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>
 
// Global array for storing results
volatile uint16_t results[6];

/*
 * 1. COUNTDOWN PATTERN: func(x - 1)
 * Classic factorial with exact (n - 1) pattern
 */
uint16_t countdown_by_one(uint8_t n) {
    // Termination condition
    if (n <= 1) {
        return 1;
    }
    
    // Exactly this pattern: countdown_by_one(n - 1)
    return n * countdown_by_one(n - 1);
}

/*
 * 2. COUNTDOWN PATTERN: func(x - 3)
 * Countdown with larger step
 */
uint8_t countdown_by_three(uint8_t n) {
    // Termination condition
    if (n <= 3) {
        return n;
    }
    
    // Exactly this pattern: countdown_by_three(n - 3)
    return countdown_by_three(n - 3);
}

/*
 * 3. DIVISION PATTERN: func(x / 2)
 * Binary search with integer division
 */
uint8_t binary_divide_by_two(uint8_t n) {
    // Termination condition
    if (n <= 1) {
        return n;
    }
    
    // LED signaling
    PORTB = n;
    _delay_ms(10);
    
    // Exactly this pattern: binary_divide_by_two(n / 2)
    return binary_divide_by_two(n / 2);
}

/*
 * 4. DIVISION PATTERN: func(x / 4)
 * Division with larger divisor
 */
uint8_t divide_by_four(uint8_t n) {
    // Termination condition
    if (n <= 4) {
        return n;
    }
    
    // Exactly this pattern: divide_by_four(n / 4)
    return divide_by_four(n / 4);
}

/*
 * 5. BIT SHIFT PATTERN: func(x >> 1)
 * Division by 2 using bit shift
 */
uint8_t bitshift_by_one(uint8_t n) {
    // Termination condition
    if (n <= 1) {
        return n;
    }
    
    // LED signaling
    PORTB = (1 << n);
    _delay_ms(5);
    
    // Exactly this pattern: bitshift_by_one(n >> 1)
    return bitshift_by_one(n >> 1);
}

/*
 * 6. BIT SHIFT PATTERN: func(x >> 3)
 * Division by 8 (2^3) using bit shift
 */
uint8_t bitshift_by_three(uint8_t n) {
    // Termination condition
    if (n <= 8) {
        return n;
    }
    
    // LED signaling
    PORTB = (n >> 3);
    _delay_ms(5);
    
    // Exactly this pattern: bitshift_by_three(n >> 3)
    return bitshift_by_three(n >> 3);
}

/*
 * WRAPPER FUNCTIONS WITH KNOWN VALUES
 */
void test_countdown_one(void) {
    results[0] = countdown_by_one(5);  // 5! = 120
}

void test_countdown_three(void) {
    results[1] = countdown_by_three(15);  // 15 -> 12 -> 9 -> 6 -> 3
}

void test_divide_two(void) {
    results[2] = binary_divide_by_two(32);  // 32 -> 16 -> 8 -> 4 -> 2 -> 1
}

void test_divide_four(void) {
    results[3] = divide_by_four(64);  // 64 -> 16 -> 4
}

void test_bitshift_one(void) {
    results[4] = bitshift_by_one(128);  // 128 >> 1 -> 64 >> 1 -> ... -> 1
}

void test_bitshift_three(void) {
    results[5] = bitshift_by_three(512);  // 512 >> 3 -> 64 >> 3 -> 8
}

/*
 * MAIN FUNCTION
 */
int main(void) {
    // Initialize I/O ports
    DDRB = 0xFF;   // PORTB as output
    PORTB = 0x00;  // Initial state
    
    // Enable interrupts
    sei();
    
    // Call all recursive functions with known values
    
    // 1. Countdown by 1, depth: 6 (5->4->3->2->1->0)
    test_countdown_one();
    
    // 2. Countdown by 3, depth: 6 (15->12->9->6->3->0)
    test_countdown_three();
    
    // 3. Division by 2, depth: 6 (32->16->8->4->2->1)
    test_divide_two();
    
    // 4. Division by 4, depth: 4 (64->16->4->1)
    test_divide_four();
    
    // 5. Bit shift by 1 (division by 2), depth: 8 (128->64->32->16->8->4->2->1)
    test_bitshift_one();
    
    // 6. Bit shift by 3 (division by 8), depth: 4 (512->64->8->1)
    test_bitshift_three();
    
    // Display results with LEDs
    while (1) {
        for (uint8_t i = 0; i < 6; i++) {
            // Show result on ports
            PORTB = (uint8_t)(results[i] & 0xFF);
            _delay_ms(500);
            
            // Pause between results
            PORTB = 0x00;
            _delay_ms(200);
        }
        
        // Longer pause between cycles
        _delay_ms(2000);
    }
    
    return 0;
}

// Izmantojot .su failu un manuāli aprēķinot garāko ceļu, maksimālais steka patēriņš ir 203 baiti
// Izmantojot avr-size priekš elf faila un manuāli saskaitot .data un .bss, maksimālais patēriņš ir 12 baiti