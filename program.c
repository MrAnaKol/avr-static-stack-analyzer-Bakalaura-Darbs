
#include <avr/io.h>
#include <util/delay.h>

void delay_function(int level) {
    // Lokāls masīvs, kas tiks ievietots stekā
    uint8_t buffer[32];

    // Vienkāršs cikls, lai masīvs nepaliktu optimizēts ārā
    for (int i = 0; i < 32; i++) {
        buffer[i] = i + level;
    }

    // Rekurzīvs izsaukums (lielāka steka slodze)
    if (level > 0) {
        delay_function(level - 1);
    }
}

int main(void) {
    DDRB |= (1 << PB0); // PB0 kā izeja

    while (1) {
        PORTB ^= (1 << PB0); // pārslēdz LED stāvokli
        int a = 3;
        delay_function(a);   // izsauc funkciju, kas izmanto steku
        _delay_ms(500);
    }
}

// Izmantojot .su failu un manuāli aprēķinot garāko ceļu, maksimālais steka patēriņš ir 180 baiti
// Izmantojot avr-size priekš elf faila un manuāli saskaitot .data un .bss, maksimālais patēriņš ir 0 baiti