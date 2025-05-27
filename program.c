
#include <avr/io.h>
#include <util/delay.h>

void delay_function(int level) {
    // Local array that will be placed on the stack
    uint8_t buffer[32];

    // Simple loop so the array doesn't get optimized out
    for (int i = 0; i < 32; i++) {
        buffer[i] = i + level;
    }

    // Recursive call (higher stack load)
    if (level > 0) {
        delay_function(level - 1);
    }
}

int main(void) {
    DDRB |= (1 << PB0); // PB0 kā izeja

    while (1) {
        PORTB ^= (1 << PB0); // PB0 as output
        int a = 3;
        delay_function(a);   // call function that uses stack
        _delay_ms(500);
    }
}

// Izmantojot .su failu un manuāli aprēķinot garāko ceļu, maksimālais steka patēriņš ir 180 baiti
// Izmantojot avr-size priekš elf faila un manuāli saskaitot .data un .bss, maksimālais patēriņš ir 0 baiti