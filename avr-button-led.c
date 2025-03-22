/*
 * AVR Button Input and LED Control
 * 
 * This program reads the state of a button connected to PORTD2 and
 * controls an LED connected to PORTB5 accordingly.
 * 
 * When the button is pressed, the LED turns on.
 * When the button is released, the LED turns off.
 * 
 * Connections:
 * - Button: Connect between PORTD2 (Arduino digital pin 2) and GND
 *   (Enable internal pull-up resistor in code)
 * - LED: Connect to PORTB5 (Arduino digital pin 13) with current-limiting resistor
 * 
 * Microcontroller: ATmega328P
 * Clock: 16 MHz
 */

#include <avr/io.h>

int main(void) {
    // Set PORTB5 (LED pin) as output
    DDRB |= (1 << DDB5);
    
    // Set PORTD2 (button pin) as input
    DDRD &= ~(1 << DDD2);
    
    // Enable pull-up resistor on PORTD2
    // This makes the pin read HIGH when button is not pressed
    PORTD |= (1 << PORTD2);
    
    // Main program loop
    while (1) {
        // Check if button is pressed (PIND2 will be 0 when pressed)
        if (!(PIND & (1 << PIND2))) {
            // Button is pressed, turn on LED
            PORTB |= (1 << PORTB5);
        } else {
            // Button is not pressed, turn off LED
            PORTB &= ~(1 << PORTB5);
        }
    }
    
    return 0;
}
