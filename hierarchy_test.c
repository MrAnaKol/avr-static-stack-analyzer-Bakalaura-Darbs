#include <avr/io.h>
#include <util/delay.h>

// Level 3 functions (deepest)
void blink_led(uint8_t count) {
    uint8_t temp[4];
    
    for (uint8_t i = 0; i < count; i++) {
        PORTB |= (1 << PB0);
        temp[i % 4] = i;
        _delay_ms(100);
        PORTB &= ~(1 << PB0);
        _delay_ms(100);
    }
}

void write_eeprom(uint8_t value) {
    uint8_t buffer[6];
    
    buffer[0] = value;
    buffer[1] = value + 1;
    buffer[2] = value + 2;
    
    // Simulate EEPROM write
    for (uint8_t i = 0; i < 3; i++) {
        PORTB = buffer[i];
        _delay_ms(50);
    }
}

// Level 2 functions 
void sensor_reading(void) {
    uint8_t reading_buffer[12];
    uint8_t sensor_value = 0x55;  // Simulated value
    
    // Process reading
    for (uint8_t i = 0; i < 12; i++) {
        reading_buffer[i] = sensor_value + i;
    }
    
    // Send to indicator functions
    blink_led(reading_buffer[0] >> 4);
    write_eeprom(reading_buffer[5]);
}

void data_processing(void) {
    uint16_t data_buffer[8];
    uint8_t processed[16];
    
    // Fill buffer with data
    for (uint8_t i = 0; i < 8; i++) {
        data_buffer[i] = 0x100 + i;
    }
    
    // Process data
    for (uint8_t i = 0; i < 16; i++) {
        processed[i] = data_buffer[i % 8] & 0xFF;
    }
    
    // Send to output functions
    blink_led(3);
    write_eeprom(processed[0]);
}

// Level 1 function (called from main)
void system_task(void) {
    uint8_t task_data[24];
    uint16_t timestamp = 0x1234;
    
    // Initialize task data
    for (uint8_t i = 0; i < 24; i++) {
        task_data[i] = i;
    }
    
    // Call subsystem functions
    sensor_reading();
    data_processing();
    
    // Update timestamp
    timestamp += 1;
    task_data[0] = timestamp & 0xFF;
}

// Main function (Level 0)
int main(void) {
    // Initialize
    DDRB = 0xFF;  // All pins as output
    
    while (1) {
        system_task();
        _delay_ms(2000);
    }
    
    return 0;
}

// Izmantojot .su failu un manuāli aprēķinot garāko ceļu, maksimālais steka patēriņš ir 125 baiti
// Izmantojot avr-size priekš elf faila un manuāli saskaitot .data un .bss, maksimālais patēriņš ir 0 baiti