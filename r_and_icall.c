#include <avr/io.h>
#include <avr/interrupt.h>

// Funkciju prototipi
void led_on(void);
void led_off(void);
void delay_ms(uint16_t ms);

// Funkciju norāžu tips
typedef void (*funkcija_ptr)(void);

// Funkciju norāžu masīvs
funkcija_ptr funkcijas[2] = {
    led_on,
    led_off
};

int main(void) {
    // Iestatām LED izvadu kā izeju (piemēram, PORTB5 - Arduino UNO iebūvētā LED)
    DDRB |= (1 << DDB5);
    
    uint8_t indekss = 0;
    
    while (1) {
        // Tiešs funkcijas izsaukums (kompilators izmanto rcall)
        delay_ms(500);
        
        // Netiešs funkcijas izsaukums (kompilators izmanto icall)
        funkcijas[indekss]();
        
        // Mainām indeksu nākamajai funkcijai
        indekss = (indekss + 1) % 2;
    }
    
    return 0;
}

// LED ieslēgšanas funkcija
void led_on(void) {
    PORTB |= (1 << PORTB5);  // Ieslēdz LED
}

// LED izslēgšanas funkcija
void led_off(void) {
    PORTB &= ~(1 << PORTB5);  // Izslēdz LED
}

// Aizkaves funkcija
void delay_ms(uint16_t ms) {
    // Vienkāršs aizkaves cikls
    // Reālā programmā labāk izmantot taimeri
    volatile uint16_t i, j;
    for (i = 0; i < ms; i++) {
        for (j = 0; j < 100; j++) {
            asm volatile ("nop");
        }
    }
}

// Alternatīvs veids, kā izmantot inline assembly ar icall un rcall
void inline_asm_demo(void) {
    asm volatile (
        // Tiešs rcall piemērs
        "rcall led_on\n\t"
        
        // icall piemērs (pieņemot, ka Z reģistrā ir funkcijas adrese)
        "ldi r30, lo8(led_off)\n\t"  // Ielādē funkcijas adresi Z reģistrā
        "ldi r31, hi8(led_off)\n\t"
        "icall\n\t"
    );
}

// Izmantojot .su failu un manuāli aprēķinot garāko ceļu, maksimālais steka patēriņš ir 15 baiti
// Izmantojot avr-size priekš elf faila un manuāli saskaitot .data un .bss, maksimālais patēriņš ir 4 baiti