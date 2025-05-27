#include <avr/io.h>
#include <avr/interrupt.h>

// Function prototypes
void led_on(void);
void led_off(void);
void delay_ms(uint16_t ms);

// Function pointer type
typedef void (*funkcija_ptr)(void);

// Function pointer array
funkcija_ptr funkcijas[2] = {
    led_on,
    led_off
};

int main(void) {
    // Set LED output as output (e.g., PORTB5 - Arduino UNO built-in LED)
    DDRB |= (1 << DDB5);
    
    uint8_t indekss = 0;
    
    while (1) {
        // Direct function call (compiler uses rcall)
        delay_ms(500);
        
        // Indirect function call (compiler uses icall)
        funkcijas[indekss]();
        
        // Change index for next function
        indekss = (indekss + 1) % 2;
    }
    
    return 0;
}

// LED turn-on function
void led_on(void) {
    PORTB |= (1 << PORTB5);  // Turn on LED
}

// LED turn-off function
void led_off(void) {
    PORTB &= ~(1 << PORTB5);  // Turn off LED
}

// Delay function
void delay_ms(uint16_t ms) {
    // Simple delay loop
    // In real programs it's better to use a timer
    volatile uint16_t i, j;
    for (i = 0; i < ms; i++) {
        for (j = 0; j < 100; j++) {
            asm volatile ("nop");
        }
    }
}

// Alternative way to use inline assembly with icall and rcall
void inline_asm_demo(void) {
    asm volatile (
        // Direct rcall example
        "rcall led_on\n\t"
        
        // icall example (assuming Z register contains function address)
        "ldi r30, lo8(led_off)\n\t"  // Load function address to Z register
        "ldi r31, hi8(led_off)\n\t"
        "icall\n\t"
    );
}

// Izmantojot .su failu un manuāli aprēķinot garāko ceļu, maksimālais steka patēriņš ir 15 baiti
// Izmantojot avr-size priekš elf faila un manuāli saskaitot .data un .bss, maksimālais patēriņš ir 4 baiti