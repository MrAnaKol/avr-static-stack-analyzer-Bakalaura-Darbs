/*
 * AVR ADC and PWM Example
 * 
 * This program reads an analog value from a sensor connected to ADC0 (PORTA0)
 * and uses that value to control the brightness of an LED using PWM on OC0A (PORTD6).
 * 
 * Connections:
 * - Analog sensor (e.g., potentiometer): Connect to ADC0 (Arduino analog pin A0)
 * - LED: Connect to OC0A/PORTD6 (Arduino digital pin 6) with current-limiting resistor
 * 
 * Microcontroller: ATmega328P
 * Clock: 16 MHz
 */

#include <avr/io.h>

// Function to initialize ADC
void adc_init(void) {
    // Set ADC reference voltage to AVCC (5V)
    ADMUX = (1 << REFS0);
    
    // Enable ADC and set prescaler to 128 (16MHz/128 = 125kHz)
    // ADC clock must be between 50kHz and 200kHz for maximum resolution
    ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);
}

// Function to read ADC value from a specified channel
uint16_t adc_read(uint8_t channel) {
    // Select ADC channel with safety mask
    ADMUX = (ADMUX & 0xF0) | (channel & 0x0F);
    
    // Start single conversion
    ADCSRA |= (1 << ADSC);
    
    // Wait for conversion to complete
    while (ADCSRA & (1 << ADSC));
    
    // Return ADC value
    return ADC;
}

// Function to initialize PWM (Timer0, Fast PWM mode)
void pwm_init(void) {
    // Set OC0A (PORTD6) as output
    DDRD |= (1 << DDD6);
    
    // Set Fast PWM mode, non-inverting output on OC0A
    TCCR0A = (1 << COM0A1) | (1 << WGM01) | (1 << WGM00);
    
    // Set clock source with no prescaling
    TCCR0B = (1 << CS00);
    
    // Initialize OCR0A to 0 (LED off)
    OCR0A = 0;
}

int main(void) {
    uint16_t adc_value;
    uint8_t pwm_value;
    
    // Initialize ADC and PWM
    adc_init();
    pwm_init();
    
    while (1) {
        // Read analog value from ADC0
        adc_value = adc_read(0);
        
        // Convert 10-bit ADC value (0-1023) to 8-bit PWM value (0-255)
        pwm_value = adc_value >> 2;
        
        // Set PWM duty cycle
        OCR0A = pwm_value;
    }
    
    return 0;
}
