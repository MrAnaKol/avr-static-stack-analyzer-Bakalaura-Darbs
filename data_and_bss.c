#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>

// =============================================================================
// .data sekcija - inicializēti globālie/statiskie mainīgie
// =============================================================================

// Globālie inicializēti mainīgie → .data
int sensor_threshold = 500;                    
char device_name[] = "ATmega328P_v1.0";       
uint8_t status_flags = 0x55;                  
float calibration_factor = 1.023;             

// Inicializēts masīvs → .data
uint16_t lookup_table[8] = {
    100, 200, 300, 400, 500, 600, 700, 800    
};

// Konfigurācijas struktūra → .data
struct config {
    uint8_t mode;
    uint16_t interval;
    char id[4];
} system_config = {1, 1000, "SYS"};           

// Statiski inicializēti mainīgie → .data  
static const uint8_t pin_mapping[4] = {2, 3, 4, 5};  
static int error_count = 0;                   

// =============================================================================
// .bss sekcija - neinicializēti globālie/statiskie mainīgie
// =============================================================================

// Globālie neinicializēti mainīgie → .bss
volatile uint16_t adc_reading;                 
int temperature;                               
uint32_t uptime_seconds;                       
char message_buffer[64];                       

// Neinicializēts masīvs → .bss
uint8_t sensor_history[32];                    

// Statiski neinicializēti mainīgie → .bss
static uint16_t measurement_buffer[16];        
static char debug_log[128];                    
static volatile uint8_t timer_flag;            

// Struktūra bez inicializācijas → .bss
struct measurement {
    uint16_t value;
    uint8_t timestamp;
    uint8_t quality;
} current_measurement;                         

// Mainīgie, kas eksplicīti inicializēti ar 0 → .bss (ne .data!)
int zero_initialized = 0;                     
static char empty_string[32] = {0};           

// =============================================================================
// Funkcijas
// =============================================================================

// ADC interrupt handler - izmanto .bss mainīgos
ISR(ADC_vect) {
    adc_reading = ADC;
    timer_flag = 1;
}

void init_hardware(void) {
    // Initialize ADC
    ADMUX = (1 << REFS0);  // AVCC reference
    ADCSRA = (1 << ADEN) | (1 << ADIE) | (1 << ADPS2) | (1 << ADPS1);
    
    // Initialize Timer0 for delays
    TCCR0A = 0;
    TCCR0B = (1 << CS02) | (1 << CS00);  // Prescaler 1024
    
    // Initialize pins according to mapping (.data)
    for(int i = 0; i < 4; i++) {
        DDRD |= (1 << pin_mapping[i]);
    }
    
    sei();  // Enable interrupts
}

void update_sensor_history(uint16_t value) {
    // Shift history array (.bss)
    for(int i = 31; i > 0; i--) {
        sensor_history[i] = sensor_history[i-1];
    }
    sensor_history[0] = (uint8_t)(value >> 2);  // Store upper 8 bits
}

uint16_t apply_calibration(uint16_t raw_value) {
    // Use .data calibration factor
    float calibrated = (float)raw_value * calibration_factor;
    return (uint16_t)calibrated;
}

void log_measurement(uint16_t value) {
    static uint8_t log_index = 0;  // Static in function → .bss
    
    // Store in measurement buffer (.bss)
    measurement_buffer[log_index] = value;
    log_index = (log_index + 1) % 16;
    
    // Update measurement struct (.bss)
    current_measurement.value = value;
    current_measurement.timestamp = (uint8_t)(uptime_seconds & 0xFF);
    current_measurement.quality = (value > sensor_threshold) ? 1 : 0;  // Use .data threshold
}

void process_sensor_data(void) {
    if(timer_flag) {
        timer_flag = 0;
        
        // Apply calibration using .data factor
        uint16_t calibrated_value = apply_calibration(adc_reading);
        
        // Check against threshold (.data)
        if(calibrated_value > sensor_threshold) {
            status_flags |= 0x01;  // Set sensor active flag (.data)
            
            // Use lookup table (.data) for processing
            uint8_t table_index = (calibrated_value / 100) % 8;
            uint16_t adjusted_value = lookup_table[table_index];
            
            // Store in history (.bss)
            update_sensor_history(adjusted_value);
            log_measurement(adjusted_value);
            
            // Calculate temperature (.bss)
            temperature = (int)(calibrated_value / 10) - 20;
        } else {
            status_flags &= ~0x01;  // Clear sensor active flag
            error_count++;  // Increment static error counter (.data)
        }
        
        // Update uptime (.bss)
        uptime_seconds++;
    }
}

void create_status_message(void) {
    // Create message in .bss buffer using .data device name
    char temp_str[16];
    
    // Convert values to strings (simplified)
    temp_str[0] = '0' + (temperature / 10);
    temp_str[1] = '0' + (temperature % 10);
    temp_str[2] = '\0';
    
    // Copy device name (.data) to message buffer (.bss)
    for(int i = 0; i < 15 && device_name[i] != '\0'; i++) {
        message_buffer[i] = device_name[i];
    }
    message_buffer[15] = ':';
    message_buffer[16] = ' ';
    
    // Append temperature
    message_buffer[17] = temp_str[0];
    message_buffer[18] = temp_str[1];
    message_buffer[19] = 'C';
    message_buffer[20] = '\0';
}

int main(void) {
    init_hardware();
    
    // Initialize system config (.data) if needed
    system_config.interval = 500;  // Change default interval
    
    while(1) {
        // Start ADC conversion
        ADCSRA |= (1 << ADSC);
        
        // Process data when available
        process_sensor_data();
        
        // Create status message periodically
        if((uptime_seconds % 10) == 0) {  // Every 10 seconds
            create_status_message();
        }
        
        // Blink LED based on status (.data)
        if(status_flags & 0x01) {
            PORTD |= (1 << pin_mapping[0]);   // LED on
            _delay_ms(100);
            PORTD &= ~(1 << pin_mapping[0]);  // LED off
        }
        
        _delay_ms(system_config.interval);  // Use .data config
    }
    
    return 0;
}

// Izmantojot .su failu un manuāli aprēķinot garāko ceļu, maksimālais steka patēriņš ir 68 baiti
// Izmantojot avr-size priekš elf faila un manuāli saskaitot .data un .bss, maksimālais patēriņš ir 356 baiti