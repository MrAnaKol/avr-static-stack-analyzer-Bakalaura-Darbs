# AVR Steka Analizators
### Statiskais steka izmantojuma analizators AVR mikrokontrolieriem
Visaptverošs rīks AVR mikrokontrolieru programmu steka atmiņas izmantojuma analīzei bez koda izpildes. Izstrādāts, lai palīdzētu iegulto sistēmu izstrādātājiem novērst steka pārplūdes problēmas resursu ierobežotās vidēs.

# Instalēt the AVR toolchain
```bash
sudo apt install gcc-avr binutils-avr avr-libc
```

# Instalēt Python
```bash
sudo apt install python3 python3-pip
```

# Pārbaude vai ir nepieciešami rīki
```bash
avr-gcc --version
avr-objdump --version
avr-size --version
python3 --version
```

# Pamata izmantojums
```bash
python3 avr-stack-analyzer-static.py program.c -m atmega328p -r 2048 -o O0
```

# Palīdzības parādīšana (rāda visus pieejamos karogus un to aprakstus)
```bash
python3 avr-stack-analyzer-static.py --help
```

# Pieiejami karogi
* -h vai --help parāda palīdzības ziņojumu ar visu argumentu aprakstiem
* -m vai --mcu norāda mikrokontrolleru tipu (noklusējums: atmega328p)
* -r vai --ram norāda RAM izmēru baitos (noklusējums: 2048)
* -o vai --optimization norāda optimizācijas līmeni: O0, O1, O2, O3, Os, Og, Ofast, Oz (noklusējums: O0)
* -c vai --compiler-flags ļauj nodot papildu kompilatora karogus
* -l vai --log-level norāda logging līmeni (noklusējums: warning)

## avr-button-led.c (4 baiti steks un 0 baiti .data un .bss)
Vienkāršākā testa programma, kas implementē pamata funkcionalitāti bez funkciju izsaukumiem. Programma nolasa pogas stāvokli un kontrolē LED. Šis tests pārbauda analizatora spēju apstrādāt minimālas steka prasības un pamata I/O operācijas.

## avr-adc-pwm.c (12 baiti steks un 0 baiti .data un .bss)
Pamata sensoru nolasīšanas un PWM (Pulse Width Modulation) kontroles programma ar vairākām funkcijām. Tests pārbauda analizatora spēju analizēt funkciju izsaukumu ķēdes ar lokālajiem mainīgajiem un parametru nodošanu.

## r_and_icall.c (15 baiti steks un 4 baiti .data un .bss)
Specializēts tests netiešo izsaukumu (ICALL) un relatīvo izsaukumu (RCALL) analīzei. Programma izmanto funkciju rādītāju masīvu, kas rada netiešos izsaukumus asemblera līmenī. Šis tests pārbauda analizatora spēju rekonstruēt izsaukumu grafu sarežģītos gadījumos.

## data_and_bss.c (68 baiti steks un 356 baiti .data un .bss)
Kompleksa programma ar globālajiem mainīgajiem, statiskie mainīgie, un pārtraukumu apstrādes funkcijām. Tests pārbauda analizatora spēju aprēķināt pieejamo steka telpu, ņemot vērā .data un .bss sekciju izmērus.

## hierarchy_test.c (125 baiti steks un 0 baiti .data un .bss)
Daudzlīmeņu funkciju hierarhijas tests ar četriem izsaukumu līmeņiem. Programma demonstrē dziļu funkciju izsaukumu ķēdi ar lokālajiem masīviem katrā līmenī. Tests pārbauda maksimālā steka ceļa aprēķināšanas precizitāti.

## complex_test.c (114 baiti steks un 0 baiti .data un .bss)
Sarežģīts tests ar rekursīvām funkcijām, vairākiem funkciju izsaukumu ceļiem un lieliem lokālajiem masīviem. Ietver faktoriāla aprēķinu ar rekursiju un vairākas palīgfunkcijas ar atšķirīgiem steka patēriņiem.

## program.c (180 baiti steks un 0 baiti .data un .bss)
Rekursīvas delay_function tests ar lokālo masīvu un parametru atkarīgu rekursijas dziļumu. Tests pārbauda analizatora spēju identificēt rekursijas dziļumu un aprēķināt kopējo rekursīvo steka patēriņu.

## recursion.c (203 baiti steks un 12 baiti .data un .bss)
Visaptverošs rekursijas testa komplekts ar sešām dažādām rekursīvām funkcijām, kas implementē dažādus samazināšanas modeļus: atskaitīšanu (n-1, n-3), dalīšanu (n/2, n/4), un bitu nobīdes (n>>1, n>>3). Tests pārbauda analizatora spēju atpazīt un pareizi klasificēt dažādus rekursijas tipus.

# Veic AVR steka analizatora analīzi visiem C failiem un izvada kompaktu pārskatu
Šis skripts automātiski izpilda AVR steka analizatoru visiem C failiem direktorijā un izvada kompaktu rezultātu pārskatu.
```bash
python3 test.py
```

# Informācija par darbu
Izstrādāts kā bakalaura darbs Ventspils Augstskolai 2025.
Autors: Anatolijs Koļesņevs  
Zinātniskais vadītājs: Mg.sc.ing. Jānis Šmēdiņš  
