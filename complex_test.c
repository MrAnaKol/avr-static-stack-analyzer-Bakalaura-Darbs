#include <avr/io.h>
#include <util/delay.h>

// Recursive function
uint32_t factorial(uint8_t n) {
    uint8_t temp = n;
    
    if (n <= 1) {
        return 1;
    }
    
    return n * factorial(n - 1);
}

// Helper functions
uint16_t multiply(uint8_t a, uint8_t b) {
    uint16_t result = 0;
    uint8_t buffer[4];
    
    for (uint8_t i = 0; i < b; i++) {
        result += a;
        buffer[i % 4] = result & 0xFF;
    }
    
    return result;
}

uint8_t divide(uint16_t dividend, uint8_t divisor) {
    uint8_t temp_array[6];
    uint8_t quotient = 0;
    
    while (dividend >= divisor) {
        dividend -= divisor;
        quotient++;
        temp_array[quotient % 6] = quotient;
    }
    
    return quotient;
}

void math_operations(uint8_t value) {
    uint32_t fact_result;
    uint16_t mult_result;
    uint8_t div_result;
    uint8_t local_buffer[20];
    
    // Multiple function calls
    fact_result = factorial(value);
    mult_result = multiply(value, 3);
    div_result = divide(fact_result, value);
    
    // Store results in local buffer
    local_buffer[0] = fact_result & 0xFF;
    local_buffer[1] = mult_result & 0xFF;
    local_buffer[2] = div_result;
    
    // Output to PORTB
    PORTB = local_buffer[0];
    _delay_ms(100);
}

int main(void) {
    // Set up PORTB as output
    DDRB = 0xFF;
    
    while (1) {
        math_operations(5);  // 5! will create deep recursion
        _delay_ms(1000);
    }
    
    return 0;
}

// Izmantojot .su failu un manuāli aprēķinot garāko ceļu, maksimālais steka patēriņš ir 114 baiti
// Izmantojot avr-size priekš elf faila un manuāli saskaitot .data un .bss, maksimālais patēriņš ir 0 baiti