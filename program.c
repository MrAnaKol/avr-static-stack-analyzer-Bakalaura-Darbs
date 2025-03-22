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
        delay_function(3);   // izsauc funkciju, kas izmanto steku
        _delay_ms(500);
    }
}
