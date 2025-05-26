/*
 * AVR rekursijas piemēri specifiskiem pattern tipiem
 * Mērķis: pārbaudīt skriptu pattern recognition
 * MCU: atmega328p
 */

 #include <avr/io.h>
 #include <avr/interrupt.h>
 #include <util/delay.h>
 
 // Globālais masīvs rezultātu uzglabāšanai
 volatile uint16_t results[6];
 
 /*
  * 1. ATSKAITĪŠANAS PATTERN: func(x - 1)
  * Klasiskā faktoriāla ar tieši (n - 1) šablonu
  */
 uint16_t countdown_by_one(uint8_t n) {
     // Beigu nosacījums
     if (n <= 1) {
         return 1;
     }
     
     // Tieši šis šablons: countdown_by_one(n - 1)
     return n * countdown_by_one(n - 1);
 }
 
 /*
  * 2. ATSKAITĪŠANAS PATTERN: func(x - 3)
  * Atskaitīšana ar lielāku soli
  */
 uint8_t countdown_by_three(uint8_t n) {
     // Beigu nosacījums
     if (n <= 3) {
         return n;
     }
     
     // Tieši šis šablons: countdown_by_three(n - 3)
     return countdown_by_three(n - 3);
 }
 
 /*
  * 3. DALĪŠANAS PATTERN: func(x / 2)
  * Binārā meklēšana ar integer dalīšanu
  */
 uint8_t binary_divide_by_two(uint8_t n) {
     // Beigu nosacījums
     if (n <= 1) {
         return n;
     }
     
     // LED signalizācija
     PORTB = n;
     _delay_ms(10);
     
     // Tieši šis šablons: binary_divide_by_two(n / 2)
     return binary_divide_by_two(n / 2);
 }
 
 /*
  * 4. DALĪŠANAS PATTERN: func(x / 4)
  * Dalīšana ar lielāku dalītāju
  */
 uint8_t divide_by_four(uint8_t n) {
     // Beigu nosacījums
     if (n <= 4) {
         return n;
     }
     
     // Tieši šis šablons: divide_by_four(n / 4)
     return divide_by_four(n / 4);
 }
 
 /*
  * 5. BIT SHIFT PATTERN: func(x >> 1)
  * Dalīšana ar 2 izmantojot bit shift
  */
 uint8_t bitshift_by_one(uint8_t n) {
     // Beigu nosacījums
     if (n <= 1) {
         return n;
     }
     
     // LED signalizācija
     PORTB = (1 << n);
     _delay_ms(5);
     
     // Tieši šis šablons: bitshift_by_one(n >> 1)
     return bitshift_by_one(n >> 1);
 }
 
 /*
  * 6. BIT SHIFT PATTERN: func(x >> 3)
  * Dalīšana ar 8 (2^3) izmantojot bit shift
  */
 uint8_t bitshift_by_three(uint8_t n) {
     // Beigu nosacījums
     if (n <= 8) {
         return n;
     }
     
     // LED signalizācija
     PORTB = (n >> 3);
     _delay_ms(5);
     
     // Tieši šis šablons: bitshift_by_three(n >> 3)
     return bitshift_by_three(n >> 3);
 }
 
 /*
  * WRAPPER FUNKCIJAS AR ZINĀMĀM VĒRTĪBĀM
  */
 void test_countdown_one(void) {
     results[0] = countdown_by_one(5);  // 5! = 120
 }
 
 void test_countdown_three(void) {
     results[1] = countdown_by_three(15);  // 15 -> 12 -> 9 -> 6 -> 3
 }
 
 void test_divide_two(void) {
     results[2] = binary_divide_by_two(32);  // 32 -> 16 -> 8 -> 4 -> 2 -> 1
 }
 
 void test_divide_four(void) {
     results[3] = divide_by_four(64);  // 64 -> 16 -> 4
 }
 
 void test_bitshift_one(void) {
     results[4] = bitshift_by_one(128);  // 128 >> 1 -> 64 >> 1 -> ... -> 1
 }
 
 void test_bitshift_three(void) {
     results[5] = bitshift_by_three(512);  // 512 >> 3 -> 64 >> 3 -> 8
 }
 
 /*
  * GALVENĀ FUNKCIJA
  */
 int main(void) {
     // Inicializē I/O portus
     DDRB = 0xFF;   // PORTB kā izeja
     PORTB = 0x00;  // Sākuma stāvoklis
     
     // Enable interrupts
     sei();
     
     // Izsauc visas rekursīvās funkcijas ar zināmām vērtībām
     
     // 1. Atskaitīšana par 1, dziļums: 6 (5->4->3->2->1->0)
     test_countdown_one();
     
     // 2. Atskaitīšana par 3, dziļums: 6 (15->12->9->6->3->0)
     test_countdown_three();
     
     // 3. Dalīšana ar 2, dziļums: 6 (32->16->8->4->2->1)
     test_divide_two();
     
     // 4. Dalīšana ar 4, dziļums: 4 (64->16->4->1)
     test_divide_four();
     
     // 5. Bit shift par 1 (dalīšana ar 2), dziļums: 8 (128->64->32->16->8->4->2->1)
     test_bitshift_one();
     
     // 6. Bit shift par 3 (dalīšana ar 8), dziļums: 4 (512->64->8->1)
     test_bitshift_three();
     
     // Rezultātu atspoguļošana LED ar
     while (1) {
         for (uint8_t i = 0; i < 6; i++) {
             // Rāda rezultātu uz portiem
             PORTB = (uint8_t)(results[i] & 0xFF);
             _delay_ms(500);
             
             // Pauze starp rezultātiem
             PORTB = 0x00;
             _delay_ms(200);
         }
         
         // Ilgāka pauze starp cikliem
         _delay_ms(2000);
     }
     
     return 0;
 }

// Izmantojot .su failu un manuāli aprēķinot garāko ceļu, maksimālais steka patēriņš ir 203 baiti
// Izmantojot avr-size priekš elf faila un manuāli saskaitot .data un .bss, maksimālais patēriņš ir 12 baiti