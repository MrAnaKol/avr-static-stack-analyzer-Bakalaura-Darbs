import subprocess
import re
import os
import argparse
import json
import tempfile
import shutil
import logging

# Iestata žurnālošanu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('avr_stack_analyzer')

class AVRCStackAnalyzer:
    """Steka izmantojuma analizators AVR mikrokontrolieriem, pieņemot C kodu."""
    
    def __init__(self, source_file, mcu_type="atmega328p", language="en", compiler_flags=None):
        """Inicializē analizatoru ar C pirmkoda failu un mikrokontroliera tipu."""
        self.source_file = source_file
        self.mcu_type = mcu_type
        self.language = language
        self.compiler_flags = compiler_flags or []
        
        # Pagaidu direktorija kompilācijas artefaktiem
        self.temp_dir = tempfile.mkdtemp(prefix="avr_stack_analyzer_")
        self.elf_file = os.path.join(self.temp_dir, os.path.splitext(os.path.basename(source_file))[0] + ".elf")
        
        self.messages = {
            "en": {
                "compiling": "Compiling C code",
                "static_analysis": "Static Analysis",
                "predicted_usage": "Predicted stack usage",
                "bytes": "bytes",
                "error_tools": "Required tools not available",
                "check_installation": "Please check installation of",
                "compilation_failed": "Compilation failed",
            },
            "lv": {
                "compiling": "Kompilē C kodu",
                "static_analysis": "Statiskā Analīze",
                "predicted_usage": "Prognozētais steka izmantojums",
                "bytes": "baiti",
                "error_tools": "Nepieciešamie rīki nav pieejami",
                "check_installation": "Lūdzu, pārbaudiet instalāciju",
                "compilation_failed": "Kompilācija neizdevās",
            }
        }
        
        # Pārbauda, vai fails eksistē
        if not os.path.isfile(source_file):
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
        # Pārbauda, vai nepieciešamie rīki ir pieejami
        self.check_required_tools()
        
        # Iegūst mikrokontroliera atmiņas īpašības
        self.mcu_properties = self.get_mcu_properties(mcu_type)
        
        # Nolasa pirmkodu analīzei
        try:
            with open(source_file, 'r') as f:
                self.source_content = f.read()
        except:
            logger.warning("Could not read source file for analysis")
            self.source_content = ""

    def __del__(self):
        """Iztīra pagaidu failus, kad objekts tiek iznīcināts."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logger.debug(f"Cleaned up temporary directory: {self.temp_dir}")

    def _(self, key):
        """Iegūst lokalizētu ziņojumu."""
        return self.messages.get(self.language, self.messages["en"]).get(key, key)

    def check_required_tools(self):
        """Pārbauda, vai visi nepieciešamie rīki ir uzstādīti un pieejami."""
        required_tools = ["avr-gcc", "avr-objdump", "avr-size"]
        missing_tools = []
        
        for tool in required_tools:
            try:
                subprocess.run(
                    ["which", tool], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
            except subprocess.CalledProcessError:
                missing_tools.append(tool)
        
        if missing_tools:
            error_msg = f"{self._('error_tools')}: {', '.join(missing_tools)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_mcu_properties(self, mcu_type):
        """Iegūst norādītā mikrokontroliera atmiņas īpašības."""
        # Var paplašināt ar vairākiem mikrokontroliera vai ielādēt no konfigurācijas faila
        mcu_properties = {
            "atmega328p": {"ram_size": 2048, "ram_start": 0x100, "stack_top": 0x08FF},
            "atmega2560": {"ram_size": 8192, "ram_start": 0x200, "stack_top": 0x21FF},
            "attiny85": {"ram_size": 512, "ram_start": 0x60, "stack_top": 0x025F},
        }
        
        if mcu_type not in mcu_properties:
            logger.warning(f"Unknown MCU type: {mcu_type}. Using atmega328p as default.")
            return mcu_properties["atmega328p"]
        
        return mcu_properties[mcu_type]

    def compile_c_code(self, include_dirs=None, library_dirs=None):
        """Kompilē C kodu uz ELF izmantojot avr-gcc."""
        logger.info(f"{self._('compiling')}...")
        
        # Izveidot kompilatora komandu
        cmd = ["avr-gcc"]
        
        # Pievienot mikrokontroliera veidu
        cmd.extend(["-mmcu=" + self.mcu_type])
        
        # Pievieno optimizācijas līmeni un atkļūdošanas informāciju -O0, -O1, -O2, -O3, -Os, -Og
        cmd.extend(["-O0", "-g"])  # Bez optimizācijas
        
        # Pievieno karogus, lai pilnībā atspējotu funkciju ievietošanu un citas optimizācijas
        # Tas ir svarīgi precīzai izsaukumu diagrammas analīzei
        cmd.extend(["-fno-inline", "-fno-inline-small-functions"])
        
        # Pievieno steka izmantojuma karogu papildu analīzei
        cmd.extend(["-fstack-usage"])
        
        # Pievieno iekļaušanas direktorijas
        if include_dirs:
            for inc_dir in include_dirs:
                cmd.extend(["-I", inc_dir])
        
        # Pievieno bibliotēku direktorijas
        if library_dirs:
            for lib_dir in library_dirs:
                cmd.extend(["-L", lib_dir])
        
        # Pievieno papildu kompilatora karogus
        cmd.extend(self.compiler_flags)
        
        # Pievieno izvades failu
        cmd.extend(["-o", self.elf_file])
        
        # Pievieno avota failu
        cmd.append(self.source_file)
        
        print("Compiler command:", " ".join(cmd))

        # Palaiž kompilāciju
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f"Compilation output: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"{self._('compilation_failed')}: {e.stderr}")
            raise RuntimeError(f"{self._('compilation_failed')}: {e.stderr}")

    def collect_stack_usage_reports(self):
        """Savāc un parsē .su failus, kas ģenerēti ar -fstack-usage karogu."""
        # Atrod avota faila bāzes nosaukumu
        base_name = os.path.splitext(os.path.basename(self.source_file))[0]

        # Iespējamās .su faila atrašanās vietas
        possible_locations = [
            # Sākotnējais avota direktorijs
            os.path.join(os.path.dirname(self.source_file), f"{base_name}.su"),
            # Pārbauda arī ar .elf prefiksu
            os.path.join(os.path.dirname(self.source_file), f"{base_name}.elf-{base_name}.su"),
            # Pašreizējais darba direktorijs
            os.path.join(os.getcwd(), f"{base_name}.su"),
            os.path.join(os.getcwd(), f"{base_name}.elf-{base_name}.su"),
            # Pagaidu direktorijs
            os.path.join(self.temp_dir, f"{base_name}.su"),
            os.path.join(self.temp_dir, f"{base_name}.elf-{base_name}.su")
        ]

        # Mēģina atrast .su failu visās iespējamās atrašanās vietās
        su_file = None
        for location in possible_locations:
            if os.path.exists(location):
                su_file = location
                logger.debug(f"Found stack usage file at: {su_file}")
                break
        
        # Pārbauda, vai tika atrasts .su fails
        if not su_file:
            logger.warning(f"Stack usage file not found for {base_name}. Checked locations: {possible_locations}")
            return {}
        
        # Parsē .su failu
        function_usage = {}

        with open(su_file, 'r') as f:
            for line in f:
                print(f"Raw line from .su file: {line.strip()}")  # ATKLĀŠANAS drukāšana

                # Atrod pēdējo skaitlisko vērtību, kas ir steka lietojums
                match = re.search(r'(\d+)\s+\w+$', line)
                if match:
                    try:
                        usage = int(match.group(1))  # Izvilk steka lietojumu
                        # Izņem funkcijas nosaukumu, izmantojot spēcīgāku pieeju
                        func_match = re.search(r':[^:]+:([^\s:]+)\s+', line)
                        if func_match:
                            function_name = func_match.group(1)
                            function_usage[function_name] = usage
                            logger.debug(f"Function: {function_name}, Stack usage: {usage} bytes")
                        else:
                            # Atkāpšanās uz vienkāršāku parsēšanu
                            parts = line.strip().split(':')
                            if len(parts) >= 3:
                                function_name = parts[2].split()[0]
                                function_usage[function_name] = usage
                                logger.debug(f"Function: {function_name}, Stack usage: {usage} bytes")
                    except ValueError:
                        logger.warning(f"Skipping malformed line: {line.strip()}")
                else:
                    logger.warning(f"Skipping malformed line: {line.strip()}")

        if not function_usage:
            logger.warning(f"No stack usage information found in {su_file}")
        else:
            logger.info(f"Collected stack usage for {len(function_usage)} functions")
            logger.info(f"GCC reported stack usage: {function_usage}")

        return function_usage

    def disassemble_avr(self):
        """Disasamble AVR kodu izmantojot avr-objdump."""
        logger.info(f"{self._('static_analysis')}: Disassembling code...")
        
        result = subprocess.run(
            ["avr-objdump", "-d", self.elf_file], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout
    
    def find_variable_values(self):
        """Atrod sākotnējās vērtības, kas piešķirtas mainīgajiem pirmkodā."""
        # Ja nav avota saturs, atgriež tukšu vārdnīcu
        if not self.source_content:
            return {}
            
        variable_values = {}
        
        # Modelis, lai atrastu mainīgos (gan globālus, gan lokālus)
        # Atbilst int, char, uint8_t, u.c. mainīgo veidus
        assign_pattern = re.compile(r'(?:int|char|uint\d+_t|long|short|float|double)\s+(\w+)\s*=\s*(\d+)\s*;')
        
        for match in assign_pattern.finditer(self.source_content):
            var_name, value = match.groups()
            try:
                # Convert the value string to an integer
                variable_values[var_name] = int(value)
                logger.info(f"Found variable assignment: {var_name} = {value}")
            except ValueError:
                pass
                
        return variable_values
    
    def is_infinite_loop_function(self, func_name):
        """
        Nosaka, vai funkcija satur bezgalīgu ciklu, nepalielinot izsaukumu steku. Īpaši svarīgi funkcijai 'main'.
        """
        if func_name != 'main':
            return False
            
        # Meklē funkcijas definīciju
        func_def_pattern = re.compile(r'(?:\w+\s+)+' + re.escape(func_name) + r'\s*\([^)]*\)\s*{', re.DOTALL)
        
        for match in func_def_pattern.finditer(self.source_content):
            # Iegūst funkcijas sākumu
            start_pos = match.start()
            
            # Atrod atbilstošo noslēdzošo iekavu
            brace_count = 0
            in_function = False
            for i, char in enumerate(self.source_content[start_pos:]):
                if char == '{':
                    brace_count += 1
                    in_function = True
                elif char == '}':
                    brace_count -= 1
                    if in_function and brace_count == 0:
                        end_pos = start_pos + i
                        break
            
            # Iegūst funkcijas ķermeni
            func_body = self.source_content[start_pos:end_pos]
            
            # Meklē while(1) vai while(true) vai for(;;) modeli
            infinite_loop_pattern = re.compile(r'while\s*\(\s*(1|true)\s*\)|for\s*\(\s*;\s*;\s*\)')
            
            if infinite_loop_pattern.search(func_body):
                logger.info(f"Function '{func_name}' contains an infinite loop construct (not true recursion)")
                return True
                
        return False
    
    def function_calls_itself(self, func_name):
        """
        Precīzi nosaka, vai funkcija patiešām izsauc pati sevi tieši. Pārbauda tieši funkcijas izsaukuma rakstus, ne tikai nosaukuma parādīšanos.
        """
        # Izlaiž, ja nav avota satura
        if not self.source_content:
            return False
            
        # Izveido modeli, lai atrastu funkcijas definīciju un tās ķermeni
        func_def_pattern = re.compile(r'(?:\w+\s+)+' + re.escape(func_name) + r'\s*\([^)]*\)\s*{', re.DOTALL)
        
        # Meklē funkcijas definīciju
        match = func_def_pattern.search(self.source_content)
        if not match:
            return False
            
        # Iegūst funkcijas sākumu
        start_pos = match.start()
        
        # Atrod atbilstošo noslēdzošo iekavu
        brace_count = 0
        in_function = False
        end_pos = None
        
        for i, char in enumerate(self.source_content[start_pos:]):
            if char == '{':
                brace_count += 1
                in_function = True
            elif char == '}':
                brace_count -= 1
                if in_function and brace_count == 0:
                    end_pos = start_pos + i
                    break
        
        if end_pos is None:
            # Nevarēja atrast funkcijas beigas
            return False
            
        # Iegūstiet visu funkcijas ķermeni
        function_body = self.source_content[start_pos:end_pos]
        
        # Meklē funkciju izsaukuma modeļus — nosaukums un tam seko atvērtās iekavas, 
        # pārliecinoties, ka tas ir pilns vārds (nevis cita identifikatora apakšvirkne)
        call_pattern = re.compile(r'\b' + re.escape(func_name) + r'\s*\([^)]*\)', re.DOTALL)
        
        # Pirmā atbilstība ir pati funkcijas definīcija, tāpēc mums ir jāmeklē tālāk
        # Izvelk tikai funkcijas ķermeni, neietverot deklarāciju
        first_brace_pos = function_body.find('{')
        if first_brace_pos == -1:
            return False
            
        actual_body = function_body[first_brace_pos:]
        
        # Meklē paša izsaukumu funkcijas ķermenī
        if call_pattern.search(actual_body):
            logger.info(f"Confirmed function '{func_name}' directly calls itself (truly recursive)")
            return True
            
        return False
    
    def detect_recursive_functions_from_source(self, gcc_stack_usage):
        """
        Analizē pirmkodu, lai noteiktu rekursīvās funkcijas.
        Šī pieeja ir uzticamāka nekā rekursijas meklēšana assemblerī.
        
        Atgriež:
            Rekursīvu funkciju nosaukumu kopu.
        """
        recursive_funcs = set()
        
        # Iegūst sarakstu ar visām funkcijām, par kurām paziņo GCC
        known_functions = list(gcc_stack_usage.keys())
        
        # Izlaiž, ja nav avota satura
        if not self.source_content:
            return recursive_funcs
        
        logger.info("Analyzing source code for recursive functions...")
        
        # Pārbauda katru funkciju, vai tā tieši izsauc sevi, izmantojot mūsu precīzāko metodi -------------
        for func_name in known_functions:
            # Izlaiž 'main' funkciju rekursijas noteikšanai - tas ir īpašs gadījums
            if func_name == 'main':
                continue
                
            # Pārbauda, vai funkcija tieši izsauc sevi
            if self.function_calls_itself(func_name):
                recursive_funcs.add(func_name)
        
        # Šablons priekš klasiskās rekursijas samazināšanas šablona 
        # Tas meklē: if (x > 0) { func(x - 1); }
        recursive_pattern = re.compile(r'if\s*\(\s*(\w+)\s*>\s*0\s*\)\s*{[^{}]*\b(\w+)\s*\(\s*\1\s*-\s*1\s*\)', re.DOTALL)
        
        for match in recursive_pattern.finditer(self.source_content):
            param_name, func_name = match.groups()
            if func_name != 'main' and func_name in gcc_stack_usage and func_name not in recursive_funcs:
                # Dubultpārbaude, vai tas ir funkcijas ķermenī
                if self.function_calls_itself(func_name):
                    recursive_funcs.add(func_name)
                    logger.info(f"Found recursive function with decremented parameter: {func_name}")
        
        return recursive_funcs

    def find_recursive_call_limits(self, recursive_functions):
        """
        Nosaka maksimālo rekursijas dziļumu rekursīvajām funkcijām, pārbaudot avota kodu.
        
        Argumenti:
            recursive_functions: funkciju nosaukumu kopa, kas ir rekursīvi.

        Atgriež:
            Vārdnīcas kartēšanas funkciju nosaukumus līdz to maksimālajam rekursijas dziļumam.
        """
        recursion_limits = {}
        
        if not self.source_content or not recursive_functions:
            # Noklusējums priekš drošas rekursijas dziļuma visām funkcijām
            return {func: 10 for func in recursive_functions}
        
        # Iegūst sākotnējās mainīgo vērtības avota kodā
        variable_values = self.find_variable_values()
        logger.info(f"Found variable values: {variable_values}")
        
        # Katrai rekursīvai funkcijai pārbauda visas vietas, kur tās tiek izsauktas
        for func in recursive_functions:
            # Noklusējuma dziļuma vērtība
            recursion_limits[func] = 10
            
            # Meklē izsaukumus uz šo funkciju ar skaitliskām literālām vērtībām
            literal_pattern = re.compile(r'\b' + re.escape(func) + r'\s*\(\s*(\d+)\s*[,)]')
            
            # Atrod atbilstības avota kodā
            initial_values = []
            for match in literal_pattern.finditer(self.source_content):
                try:
                    # Iegūst skaitli, kas tiek nodots funkcijai
                    value = int(match.group(1))
                    initial_values.append(value)
                    logger.info(f"Found call to {func} with literal value {value}")
                except ValueError:
                    pass
            
            # Meklē izsaukumus uz šo funkciju ar mainīgajiem
            var_pattern = re.compile(r'\b' + re.escape(func) + r'\s*\(\s*(\w+)\s*[,)]')
            
            for match in var_pattern.finditer(self.source_content):
                var_name = match.group(1)
                if var_name in variable_values:
                    value = variable_values[var_name]
                    initial_values.append(value)
                    logger.info(f"Found call to {func} with variable {var_name} = {value}")
            
            # Nosaka maksimālo dziļumu, pamatojoties uz lielāko sākotnējo vērtību
            if initial_values:
                # Pievieno 1, lai ņemtu vērā bāzes gadījumu (0 līmeni)
                max_depth = max(initial_values) + 1
                recursion_limits[func] = max_depth
                logger.info(f"Set recursion limit for {func} to {max_depth} (initial value {max(initial_values)} + 1)")
        
        return recursion_limits

    def get_memory_sections(self):
        """Iegūst atmiņas sekciju informāciju izmantojot avr-size."""
        result = subprocess.run(
            ["avr-size", "-A", self.elf_file], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Parsē izvadi, lai iegūtu sekciju izmērus
        sections = {}
        for line in result.stdout.split('\n')[2:]:  # Izlaiž galvenes rindas
            parts = line.split()
            if len(parts) >= 2:
                try:
                    sections[parts[0]] = int(parts[1])
                except (IndexError, ValueError):
                    pass
        
        return sections

    def analyze_static_stack_usage(self, asm_code, gcc_stack_usage):
        """Analizē maksimālo steka izmantojumu, balstoties uz disasambleto kodu."""
        logger.info(f"{self._('static_analysis')}: Analyzing stack operations...")
        
        # Pirmkārt, atklāj rekursīvās funkcijas no avota koda - tas ir precīzāk
        recursive_functions = self.detect_recursive_functions_from_source(gcc_stack_usage)
        
        # Atrod rekursijas ierobežojumus visām rekursīvajām funkcijām
        recursion_limits = self.find_recursive_call_limits(recursive_functions)
        
        # Iegūst funkcijas no disasamblešanas
        function_pattern = re.compile(r'^[0-9a-f]+ <([^>]+)>:')
        current_function = None
        functions = {}
        current_function_lines = []
        
        for line in asm_code.split('\n'):
            # Pārbauda, vai šī ir jauna funkcija
            match = function_pattern.match(line)
            if match:
                if current_function:
                    functions[current_function] = '\n'.join(current_function_lines)
                current_function = match.group(1)
                current_function_lines = []
            
            if current_function:
                current_function_lines.append(line)
        
        # Pievieno pēdējo funkciju
        if current_function and current_function_lines:
            functions[current_function] = '\n'.join(current_function_lines)
        
        # Analizē steka izmantojumu katrai funkcijai
        function_stack_usage = {}
        call_graph = {}
        
        # Rakstu šabloni steka operācijām
        push_pattern = re.compile(r'\s+push\s+')
        pop_pattern = re.compile(r'\s+pop\s+')
        call_pattern = re.compile(r'\s+(?:call|rcall|icall)\s+(?:0x)?([0-9a-f]+)?\s*<?([^>\s]*)')
        sbiw_pattern = re.compile(r'\s+sbiw\s+r(2[89]),\s*(\d+)')  # Y rādītāja pielāgošana
        adiw_pattern = re.compile(r'\s+adiw\s+r(2[89]),\s*(\d+)')  # Y rādītāja pielāgošana
        
        # Apstrāda katras funkcijas assemblera kodu
        for function_name, function_code in functions.items():
            # Inicializē izsaukumu grafiku
            if function_name not in call_graph:
                call_graph[function_name] = []
            
            # Inicializē steka izsekošanas mainīgos
            frame_size = 0  # Vietējie mainīgie
            max_stack_size = 0  # Maksimālais izmantotais steks
            current_stack = 0  # Pašreizējais steka dziļums
            
            # Analizē katru assemblera koda rindu
            for line in function_code.split('\n'):
                # Pārbaudā funkciju izsaukumus ar šablonu
                call_match = call_pattern.search(line)
                if call_match:
                    called_function = call_match.group(2)
                    # Pievieno tikai derīgus funkciju izsaukumus
                    if called_function and called_function not in call_graph[function_name] and called_function in gcc_stack_usage:
                        call_graph[function_name].append(called_function)
                        # Pieraksta šo, lai palīdzētu atkļūdot izsaukumu grafiku
                        logger.debug(f"Found call from {function_name} to {called_function}")
                    current_stack += 2  # Izsaukums pievieno atgriešanās adresi (2 baiti)
                
                # Pārbauda tiešās steka operācijas
                if push_pattern.search(line):
                    current_stack += 1  # Katrs push pievieno 1 baitu
                elif pop_pattern.search(line):
                    current_stack -= 1  # Katrs pop noņem 1 baitu
                
                # Pārbaudām steka ietvara pielāgošanu (priekš vietējiem mainīgiem)
                sbiw_match = sbiw_pattern.search(line)
                if sbiw_match:
                    adjustment = int(sbiw_match.group(2))
                    current_stack += adjustment
                    frame_size += adjustment
                
                adiw_match = adiw_pattern.search(line)
                if adiw_match:
                    adjustment = int(adiw_match.group(2))
                    current_stack -= adjustment
                
                # Atjaunina maksimālo steka izmantojumu
                max_stack_size = max(max_stack_size, current_stack)
            
            # Izmanto vai nu šīs programmas aprēķināto vērtību, vai GCC vērtību, kura ir lielāka
            # Svarīgi, lai apstrādātu gadījumus, kad GCC labāk nosaka vietējos mainīgos
            gcc_value = gcc_stack_usage.get(function_name, 0)
            calculated_value = max_stack_size + frame_size
            
            # Saglabā lielāko no abām vērtībām
            function_stack_usage[function_name] = max(calculated_value, gcc_value)
            logger.debug(f"Function {function_name}: GCC reported {gcc_value}, calculated {calculated_value}, using {function_stack_usage[function_name]}")
        
        # Pārbauda, vai 'main' funkcijai ir bezgalīga cilpa (tas neveicina steka pieaugumu)
        if self.is_infinite_loop_function('main') and 'main' in recursive_functions:
            logger.info("Removing 'main' from recursive functions as it contains an infinite loop")
            recursive_functions.remove('main')
        
        # Manuāli koriģē izsaukumu grafiku 'main' funkcijai
        # Pārbauda 'main' funkcijas saturu, vai tajā ir izsaukumi uz zināmām funkcijām
        known_functions = list(gcc_stack_usage.keys())
        if 'main' in call_graph and not call_graph['main']:
            logger.warning("No calls detected from main(). Scanning source code for function calls.")
            
            # Meklē funkciju izsaukumus avota kodā
            for func in known_functions:
                if func != 'main' and re.search(r'\b' + re.escape(func) + r'\s*\(', self.source_content):
                    call_graph['main'].append(func)
                    logger.info(f"Found call from main to {func} in source code")
        
        # Pievieno rekursīvos pašizsaukumus izsaukumu grafikam
        for func in recursive_functions:
            if func not in call_graph:
                call_graph[func] = []
            if func not in call_graph[func]:
                call_graph[func].append(func)
                logger.info(f"Added self-call for recursive function {func}")
        
        # Izveido pilnīgu izsaukumu grafiku, iekļaujot netiešos izsaukumus
        complete_call_graph = self.build_complete_call_graph(call_graph)
        
        # Pierakstā rekursīvās funkcijas un to ierobežojumus
        logger.info(f"Detected recursive functions: {recursive_functions}")
        logger.info(f"Recursion limits: {recursion_limits}")
        
        # Analizē maksimālo steka dziļumu
        max_stack_usage = self.calculate_max_stack_usage(function_stack_usage, complete_call_graph, recursive_functions, recursion_limits)
        
        # Pievieno drošības rezervi (15%)
        safe_max_stack_usage = int(max_stack_usage * 1.15)
        
        # Detalizēti analīzes rezultāti
        analysis_results = {
            'max_stack_usage': safe_max_stack_usage,
            'raw_max_usage': max_stack_usage,
            'function_usage': function_stack_usage,
            'call_graph': complete_call_graph,
            'recursive_functions': list(recursive_functions),
            'recursion_limits': recursion_limits
        }
        
        return analysis_results

    def calculate_max_stack_usage(self, function_stack_usage, call_graph, recursive_functions, recursion_limits):
        """
        Aprēķina maksimālo steka izmantojumu, ņemot vērā rekursīvos izsaukumus.
        
        Fiksēts algoritms, kas pareizi apstrādā rekursijas dziļumus un uzkrāj steka lietojumu, izmantojot izsaukumu ķēdi.
        """
        logger.info("Calculating maximum stack usage with enhanced recursive handling...")
        
        # Steka izmantojuma izsekošanas atkļūdošana
        logger.debug(f"Function stack usage: {function_stack_usage}")
        logger.debug(f"Recursive functions: {recursive_functions}")
        logger.debug(f"Recursion depth limits: {recursion_limits}")
        
        # Aprēķina kopējo steku, ko izmanto rekursīvās funkcijas
        recursive_stack = {}
        for func in recursive_functions:
            # Iegūst vietējo steka izmantojumu šai funkcijai
            local_usage = function_stack_usage.get(func, 0)
            
            # Iegūst rekursijas dziļumu
            depth = recursion_limits.get(func, 10)
            
            # Aprēķina kopējo steku visiem rekursīvajiem izsaukumiem
            # Pirmais izsaukums nav ar atgriešanās adreses pārklājumu no iepriekšējā izsaukuma
            first_call = local_usage
            
            # Sekundārie izsaukumi ietver atgriešanās adreses pārklājumu (2 biti)
            subsequent_calls = (depth - 1) * (local_usage + 2)
            
            # Kopējais rekursīvais steks šai funkcijai
            total = first_call + subsequent_calls
            recursive_stack[func] = total
            
            logger.info(f"Recursive function {func}: depth {depth}, local usage {local_usage}, total recursive usage {total}")
        
        # Izveido memoizācijas kešu apmeklētajiem ceļiem, lai izvairītos no pārrēķināšanas
        memo = {}
        
        def get_stack_usage(func_name, call_path=None, depth=0):
            """
            Rekursīvi aprēķina steka lietojumu, izmantojot izsaukumu diagrammu.
            
            Argumenti:
                func_name: pašreizējā analizējamā funkcija
                call_path: pašreizējais izsaukuma ceļš, lai izvairītos no cikliem
                depth: pašreizējais dziļums atkļūdošanai
            
            Atgriež:
                Steka lietojumu baitos šim izsaukuma ceļam
            """
            if call_path is None:
                call_path = []
            
            # Generē kešēšanas atslēgu
            cache_key = (func_name, tuple(call_path))
            if cache_key in memo:
                return memo[cache_key]
            
            # Bāzes gadījums: funkcija nav atrasta mūsu analīzē
            if func_name not in function_stack_usage:
                logger.debug(f"{'  ' * depth}Function {func_name} not found in analysis")
                return 0
            
            # Iegūst vietējo steka izmantojumu šai funkcijai
            local_usage = function_stack_usage[func_name]
            logger.debug(f"{'  ' * depth}Function {func_name}: local usage {local_usage}")
            
            # Ja tas ir rekursīvs funkcija, izmantojam iepriekš aprēķināto kopējo rekursīvo steku
            if func_name in recursive_functions and func_name not in call_path:
                total_usage = recursive_stack[func_name]
                logger.debug(f"{'  ' * depth}Recursive function {func_name}: using pre-calculated total recursive stack {total_usage}")
                
                # Pieraksta memoizācijas kešā
                memo[cache_key] = total_usage
                return total_usage
            
            # Pārbauda, vai šis ir rekursīvs izsaukums, kuru jau esam ņēmuši vērā
            if func_name in call_path:
                logger.debug(f"{'  ' * depth}Already accounted for recursive call to {func_name}")
                return 0
            
            # Aprēķina steku, ko izmanto izsauktās funkcijas
            max_call_stack = 0
            new_path = call_path + [func_name]
            
            # Pārbauda katru izsaukto funkciju
            for called_func in call_graph.get(func_name, []):
                # Izlaiž pašizsaukumus rekursīvām funkcijām, kuras jau esam apstrādājuši atsevišķi
                if called_func == func_name and func_name in recursive_functions:
                    continue
                
                # Aprēķina steku šim izsaukumam
                call_overhead = 2  # Atgriešanās adrese (2 biti AVR)
                
                # Aprēķina steku šim izsaukumam
                called_stack = get_stack_usage(called_func, new_path, depth + 1)
                
                # Atjaunina maksimālo izsaukuma steka izmantojumu
                path_stack = call_overhead + called_stack
                if path_stack > max_call_stack:
                    max_call_stack = path_stack
                    logger.debug(f"{'  ' * depth}New max call stack from {called_func}: {max_call_stack}")
            
            # Kopējais izmantojums ir vietējais izmantojums + maksimālais izsaukuma steks
            total_usage = local_usage + max_call_stack
            
            # Pieraksta memoizācijas kešā
            memo[cache_key] = total_usage
            
            logger.debug(f"{'  ' * depth}Function {func_name}: total usage {total_usage}")
            return total_usage
        
        # Aprēķina steka lietojumu no 'main'
        total_stack_usage = 0
        if 'main' in function_stack_usage:
            total_stack_usage = get_stack_usage('main')
            logger.info(f"Stack usage from entry point main: {total_stack_usage} bytes")
        
        return total_stack_usage

    def build_complete_call_graph(self, direct_call_graph):
        """Veido pilnīgu izsaukumu grafiku, ieskaitot netiešos izsaukumus."""
        # Izveidojiet tiešo izsaukumu diagrammas kopiju
        complete_graph = {}
        for func, callees in direct_call_graph.items():
            complete_graph[func] = callees.copy()
        
        # Pievieno visas funkcijas kā atslēgas, ja tās vēl nav pievienotas
        for func in direct_call_graph:
            for callee in direct_call_graph[func]:
                if callee not in complete_graph:
                    complete_graph[callee] = []
        
        return complete_graph

    def visualize_call_graph(self, call_graph, recursive_functions=None, output_file='call_graph.dot'):
        """Ģenerē DOT failu izsaukumu grafika vizualizācijai."""
        if recursive_functions is None:
            recursive_functions = []
            
        with open(output_file, 'w') as f:
            f.write('digraph CallGraph {\n')
            f.write('  node [shape=box];\n')
            
            # Stils priekš rekursīvām funkcijām
            for func in recursive_functions:
                f.write(f'  "{func}" [style=filled, fillcolor=lightcoral];\n')
            
            # Pievieno malas starp funkcijām izsaukumu grafikā
            for caller, callees in call_graph.items():
                for callee in callees:
                    # Iezīmē rekursīvos izsaukumus
                    if caller == callee:
                        f.write(f'  "{caller}" -> "{callee}" [color=red, style=bold];\n')
                    else:
                        f.write(f'  "{caller}" -> "{callee}";\n')
            
            f.write('}\n')
        
        logger.info(f"Call graph saved to {output_file}")
        logger.info("To visualize, run: dot -Tpng call_graph.dot -o call_graph.png")

    def generate_report(self, static_analysis, output_format='text'):
        """Ģenerē visaptverošu pārskatu par steka izmantojuma analīzi."""
        sections = self.get_memory_sections()
        data_size = sections.get('.data', 0) + sections.get('.bss', 0)
        
        available_stack = self.mcu_properties['ram_size'] - data_size
        
        if output_format == 'json':
            report = {
                'source_file': self.source_file,
                'mcu_type': self.mcu_type,
                'ram_size': self.mcu_properties['ram_size'],
                'data_size': data_size,
                'available_stack': available_stack,
                'static_analysis': static_analysis,
            }
            
            return json.dumps(report, indent=2)
        else:
            # Teksta atskaite
            report = [
                f"Stack Analysis Report for {os.path.basename(self.source_file)}",
                "=" * 60,
                f"MCU Type: {self.mcu_type}",
                f"RAM Size: {self.mcu_properties['ram_size']} bytes",
                f"Data Size (.data + .bss): {data_size} bytes",
                f"Available Stack Space: {available_stack} bytes",
                "",
                "Static Analysis Results:",
                "-" * 30,
                f"Predicted Maximum Stack Usage: {static_analysis['max_stack_usage']} bytes",
                f"Raw Stack Usage (without safety margin): {static_analysis['raw_max_usage']} bytes",
                f"Safety Margin: {int(available_stack - static_analysis['max_stack_usage'])} bytes",
                f"Stack Usage Percentage: {(static_analysis['max_stack_usage'] / self.mcu_properties['ram_size'] * 100):.1f}%",
                "",
                "Function Stack Usage:",
                "-" * 30,
            ]
            
            # Kārto funkcijas pēc steka lietojuma (dilstošā secībā)
            sorted_functions = sorted(
                static_analysis['function_usage'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Pievieno informāciju par funkcijām
            for function, usage in sorted_functions:
                report.append(f"{function}: {usage} bytes")
                
            # Pievieno rekursīvo funkciju informāciju, ja tāda ir
            if static_analysis['recursive_functions']:
                report.append("")
                report.append("Recursive Functions:")
                report.append("-" * 30)
                for func in static_analysis['recursive_functions']:
                    limit = static_analysis['recursion_limits'].get(func, "unknown")
                    report.append(f"{func} (recursion limit: {limit})")
            
            return "\n".join(report)

def analyze_stack(source_file, mcu_type="atmega328p", output_format="text", extra_flags=None, language="en"):
    """Analizē steka izmantojumu AVR C sākuma failam."""
    try:
        # Inicializē analizatoru
        analyzer = AVRCStackAnalyzer(source_file, mcu_type=mcu_type, language=language, compiler_flags=extra_flags)
        
        # Kompilē kodu
        analyzer.compile_c_code()
        
        # Iegūst steka lietošanas pārskatu no GCC
        gcc_stack_usage = analyzer.collect_stack_usage_reports()
        
        # Disamblē kodu
        asm_code = analyzer.disassemble_avr()
        
        # Analizē statiskās steka lietojumu
        static_analysis = analyzer.analyze_static_stack_usage(asm_code, gcc_stack_usage)
        
        # Ģenerē vizualizāciju, ja pastāv rekursīvas funkcijas
        if static_analysis['recursive_functions']:
            analyzer.visualize_call_graph(
                static_analysis['call_graph'],
                static_analysis['recursive_functions']
            )
        
        # Ģenerē atskaiti
        report = analyzer.generate_report(static_analysis, output_format)
        
        # Izdrukā pagaidu direktorijas ceļu atkļūdošanas nolūkos
        print(f"Temporary directory: {analyzer.temp_dir}")
        
        return report
        
    except Exception as e:
        logger.error(f"Error analyzing stack usage: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {e}"

def main():
    parser = argparse.ArgumentParser(description="Analyze stack usage of AVR C programs")
    parser.add_argument("source_file", help="C source file to analyze")
    parser.add_argument("-m", "--mcu", default="atmega328p", help="MCU type (default: atmega328p)")
    parser.add_argument("-f", "--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("-c", "--compiler-flags", help="Additional compiler flags")
    parser.add_argument("-l", "--language", choices=["en", "lv"], default="en", help="Output language")
    
    args = parser.parse_args()
    
    # Parsē kompilatoru karogus
    extra_flags = args.compiler_flags.split() if args.compiler_flags else None
    
    # Palaiž analīzi
    result = analyze_stack(
        args.source_file,
        mcu_type=args.mcu,
        output_format=args.format,
        extra_flags=extra_flags,
        language=args.language
    )
    
    # Izdrukā rezultātus
    print(result)

if __name__ == "__main__":
    main()