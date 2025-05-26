"""
# Instalēt the AVR toolchain
sudo apt install gcc-avr binutils-avr avr-libc

# Instalēt Python
sudo apt install python3 python3-pip

# Pārbaude vai ir nepieciešami rīki
avr-gcc --version
avr-objdump --version
avr-size --version
python3 --version

# Pamata izmantojums
python3 avr-stack-analyzer-static.py program.c -m atmega328p -r 2048 -o O0

# Palīdzības parādīšana (rāda visus pieejamos karogus un to aprakstus)
python3 avr-stack-analyzer-static.py --help

# Pieiejami karogi
-h vai --help parāda palīdzības ziņojumu ar visu argumentu aprakstiem
-m vai --mcu norāda mikrokontrolleru tipu (noklusējums: atmega328p)
-r vai --ram norāda RAM izmēru baitos (noklusējums: 2048)
-o vai --optimization norāda optimizācijas līmeni: O0, O1, O2, O3, Os, Og, Ofast, Oz (noklusējums: O0)
-c vai --compiler-flags ļauj nodot papildu kompilatora karogus
-l vai --log-level norāda logging līmeni (noklusējums: warning)
"""

import subprocess
import re
import os
import argparse
import tempfile
import shutil
import logging

def setup_logging(log_level):
    """Uzstāda žurnālošanu ar norādīto līmeni."""
    # Pārvērš string uz logging līmeni (case-insensitive)
    level_mapping = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    level_upper = log_level.upper()
    if level_upper not in level_mapping:
        raise ValueError(f"Invalid log level: {log_level}. Must be one of: {', '.join(level_mapping.keys())}")
    
    logging.basicConfig(
        level=level_mapping[level_upper],
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

logger = logging.getLogger('avr_stack_analyzer')

class AVRCStackAnalyzer:
    def __init__(self, source_file, mcu_type="atmega328p", ram_size=2048, optimization="O0", compiler_flags=None):
        """Inicializē analizatoru ar C pirmkoda failu un mikrokontroliera tipu."""
        self.source_file = source_file
        self.mcu_type = mcu_type
        self.ram_size = ram_size
        self.optimization = optimization
        self.compiler_flags = compiler_flags or []
        
        # Pagaidu direktorija kompilācijas artefaktiem
        self.temp_dir = tempfile.mkdtemp(prefix="avr_stack_analyzer_")
        self.elf_file = os.path.join(self.temp_dir, os.path.splitext(os.path.basename(source_file))[0] + ".elf")
        
        # Pārbauda, vai fails eksistē
        if not os.path.isfile(source_file):
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
        # Pārbauda, vai nepieciešamie rīki ir pieejami
        self.check_required_tools()
        
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
            error_msg = f"Missing tools: {', '.join(missing_tools)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def compile_c_code(self, include_dirs=None, library_dirs=None):
        """Kompilē C kodu uz ELF izmantojot avr-gcc."""
        logger.info("Compiling C code...")
        
        # Izveidot kompilatora komandu
        cmd = ["avr-gcc"]
        
        # Pievienot mikrokontroliera veidu
        cmd.extend(["-mmcu=" + self.mcu_type])
        
        # Validē optimizācijas līmeni
        valid_optimizations = ["O0", "O1", "O2", "O3", "Os", "Og", "Ofast", "Oz"]
        if self.optimization not in valid_optimizations:
            logger.warning(f"Invalid optimization level: {self.optimization}. Using O0 instead.")
            self.optimization = "O0"
        
        # Pievieno optimizācijas līmeni un atkļūdošanas informāciju
        cmd.extend([f"-{self.optimization}", "-g"])
        logger.info(f"Using optimization level: -{self.optimization}")
        
        # Pievieno karogus, lai pilnībā atspējotu funkciju ievietošanu un citas optimizācijas
        # Tas ir svarīgi precīzai izsaukumu grafa analīzei
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
        
        logger.info(f"Compiler command: {' '.join(cmd)}")

        # Veic kompilāciju
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
            logger.error(f"Compilation failed: {e.stderr}")
            raise RuntimeError(f"Compilation failed: {e.stderr}")

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
                logger.info(f"Raw line from .su file: {line.strip()}")
                
                # Atrod pēdējo skaitlisko vērtību, kas ir steka lietojums
                match = re.search(r'(\d+)\s+\w+$', line)
                if match:
                    try:
                        usage = int(match.group(1))
                        # Izņem funkcijas nosaukumu
                        func_match = re.search(r':[^:]+:([^\s:]+)\s+', line)
                        if func_match:
                            function_name = func_match.group(1)
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
        """ Disasamble AVR kodu izmantojot avr-objdump."""
        logger.info("Static Analysis: Disassembling code...")
        
        result = subprocess.run(
            ["avr-objdump", "-d", self.elf_file], 
            capture_output=True, 
            text=True, 
            check=True
        )
        self.asm_code = result.stdout
        return result.stdout

    def detect_recursion_from_assembly(self, asm_code, gcc_stack_usage):
        """Enhanced recursion detection with better function name normalization"""
        logger.info("Detecting recursive functions from assembly call patterns")
        
        # Funkciju adrešu kartējums
        function_addresses = {}
        func_pattern = re.compile(r'^([0-9a-f]+) <([^>]+)>:')
        
        # Savāc funkciju adreses (baitu adreses)
        for line in asm_code.split('\n'):
            match = func_pattern.match(line)
            if match:
                addr_str, func_name = match.groups()
                
                # Pārbauda, vai šī funkcija eksistē mūsu steka izmantojumā
                if func_name in gcc_stack_usage:
                    byte_addr = int(addr_str, 16)
                    word_addr = byte_addr // 2  # AVR izsaukums izmanto vārdu adreses
                    word_addr_hex = f"{word_addr:x}"
                    
                    # Glabā abus formātus un kartē uz bāzes nosaukumu
                    function_addresses[addr_str] = func_name
                    function_addresses[addr_str.lstrip('0') or '0'] = func_name
                    function_addresses[word_addr_hex] = func_name
                    function_addresses[word_addr_hex.lstrip('0') or '0'] = func_name
                    logger.debug(f"Function {func_name}: byte={addr_str}, word={word_addr_hex}")
        
        # Atrod rekursīvos izsaukumus
        recursive_functions = set()
        avr_call_pattern = re.compile(
            r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+'
            r'(?:call|rcall)\s+'  # Meklē gan call, gan rcall
            r'0x([0-9a-f]+)'
        )
        
        # Relatīvo rcall izsaukumu šablons
        rcall_relative_pattern = re.compile(
            r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+'
            r'rcall\s+\.([+-]\d+)'  # rcall .+4, rcall .-6, utt.
        )
        
        # Netiešo izsaukumu šablons (icall, eicall)
        indirect_call_pattern = re.compile(
            r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+'
            r'(?:icall|eicall)\s*'  # Netiešie izsaukumi
        )
        
        current_function = None
        logger.info("Scanning assembly for function call instructions...")
        
        # Ignorē kompilatora ģenerētās atzīmes
        ignore_labels = set()
        in_main_function = False
        
        for line in asm_code.split('\n'):
            # Pārbauda, vai ieejam funkcijā
            func_match = func_pattern.match(line)
            if func_match:
                addr_str, func_name = func_match.groups()
                
                # Atpazīst kompilatora ģenerētās atzīmes
                if '^' in func_name or func_name.startswith('.L'):
                    if in_main_function and func_name not in ignore_labels:
                        ignore_labels.add(func_name)
                        logger.debug(f"Identified compiler-generated label: {func_name}")
                    continue
                
                if func_name in gcc_stack_usage:
                    current_function = func_name
                    in_main_function = (func_name == 'main')
                    logger.debug(f"Entering function: {current_function}")
                continue
            
            if not current_function:
                continue
            
            # Meklē izsaukuma instrukcijas
            call_match = avr_call_pattern.match(line)
            if call_match:
                call_addr = call_match.group(1)
                
                # Mēģina atrast funkciju pēc izsaukuma adreses
                called_func = None
                if call_addr in function_addresses:
                    called_func = function_addresses[call_addr]
                else:
                    normalized_addr = call_addr.lstrip('0') or '0'
                    if normalized_addr in function_addresses:
                        called_func = function_addresses[normalized_addr]
                
                logger.debug(f"Call in {current_function} to {call_addr}, resolved to: {called_func}")
                
                # Pārbauda uz rekursiju
                if called_func == current_function:
                    recursive_functions.add(current_function)
                    logger.info(f"DETECTED RECURSION: {current_function} calls itself!")
                    logger.info(f"  Call site: {line.strip()}")
                continue
            
            # Meklē rcall relatīvos izsaukumus
            rcall_match = rcall_relative_pattern.match(line)
            if rcall_match:
                offset = rcall_match.group(1)
                
                # Izlaiž rcall .+0 (steka ietvara izveide)
                if offset == "+0":
                    logger.debug(f"Found stack frame setup via rcall .+0 in {current_function}")
                    continue
                    
                # Ar relatīvām adresēm nevar tieši noteikt mērķa funkciju
                logger.debug(f"Found relative rcall with offset {offset} in {current_function}")
                continue
            
            # Meklē netiešos izsaukumus (icall, eicall)
            if indirect_call_pattern.match(line):
                logger.info(f"Found indirect call (icall/eicall) in {current_function}")
                logger.debug(f"  Instruction: {line.strip()}")
                # Netiešo izsaukumu gadījumā mērķa funkciju nevar noteikt statiski
                continue
        
        if recursive_functions:
            logger.info(f"Recursive functions detected: {recursive_functions}")
        else:
            logger.info("No recursive functions detected")
        
        return recursive_functions

    def trace_parameter_through_calls(self, target_func):
        """Izseko parametru vērtības caur funkciju izsaukumu ķēdi"""
        logger.debug(f"Tracing parameter values for {target_func}")
        
        # 1. solis: Atrod kur tiek izsauktā target_func
        calling_funcs = self.find_calling_functions(target_func)
        logger.debug(f"Functions calling {target_func}: {calling_funcs}")
        
        for calling_func in calling_funcs:
            # 2. solis: Iegūst izsaucošās funkcijas definīciju  
            func_def_match = re.search(
                rf'{re.escape(calling_func)}\s*\([^)]*\)\s*{{([^{{}}]*(?:{{[^{{}}]*}}[^{{}}]*)*?)}}',
                self.source_content, re.DOTALL
            )
            
            if not func_def_match:
                continue
                
            func_body = func_def_match.group(1)
            
            # 3. solis: Atrod target_func izsaukumu šajā funkcijā
            call_match = re.search(
                rf'{re.escape(target_func)}\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)',
                func_body
            )
            
            if not call_match:
                continue
                
            param_name = call_match.group(1)
            logger.debug(f"In {calling_func}, found call: {target_func}({param_name})")
            
            # 4. solis: Pārbauda, vai param_name ir tāds pats kā funkcijas parametrs
            param_match = re.search(
                rf'{re.escape(calling_func)}\s*\(\s*([^)]*)\)',
                self.source_content
            )
            
            if param_match:
                params = param_match.group(1)
                # Pārbauda, vai param_name atrodas funkcijas parametros
                if re.search(rf'\b{re.escape(param_name)}\b', params):
                    logger.debug(f"{param_name} is a parameter of {calling_func}")
                    
                    # 5. solis: Atrod kā šī izsaucošā funkcija tiek izsaukta
                    return self.find_call_value_for_function(calling_func)
        
        return None

    def find_calling_functions(self, target_func):
        """Atrod visas funkcijas, kas izsauc mērķa funkciju"""
        calling_functions = []
        
        # Atrod visas funkcijas, kas izsauc call target_func
        call_pattern = rf'{re.escape(target_func)}\s*\('
        
         # Atrod funkciju definīcijas ar konkrētiem pamata atgriešanas tipiem
        func_pattern = r'(?:int|void|uint\d+_t|float|double)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*{'
        
        for func_match in re.finditer(func_pattern, self.source_content):
            func_name = func_match.group(1)
            func_start = func_match.start()
            
            # Atrod šīs funkcijas beigas
            brace_count = 0
            func_end = func_start
            in_function = False
            
            for i, char in enumerate(self.source_content[func_start:], func_start):
                if char == '{':
                    brace_count += 1
                    in_function = True
                elif char == '}':
                    brace_count -= 1
                    if in_function and brace_count == 0:
                        func_end = i
                        break
            
            func_body = self.source_content[func_start:func_end+1]
            
            # Pārbauda, vai šī funkcija izsauc target_func
            if re.search(call_pattern, func_body):
                calling_functions.append(func_name)
                logger.debug(f"{func_name} calls {target_func}")
        
        return calling_functions

    def find_call_value_for_function(self, func_name):
        """Atrod vērtību, kas tiek nodota funkcijas izsaukumam"""
        logger.debug(f"Looking for calls to {func_name}")
        
        # Atrod izsaukumus uz šo funkciju ar literāļu vērtībām
        call_patterns = [
            rf'{re.escape(func_name)}\s*\(\s*(\d+)\s*\)',
            rf'{re.escape(func_name)}\s*\([^,]*,\s*(\d+)\s*\)',
        ]
        
        for pattern in call_patterns:
            matches = re.finditer(pattern, self.source_content)
            for match in matches:
                value = int(match.group(1))
                logger.debug(f"Found call: {func_name}({value})")
                return value
        
        # Pārbauda arī main funkciju
        main_match = re.search(r'int\s+main\s*\([^)]*\)\s*{([^}]*(?:{[^}]*}[^}]*)*)}', 
                              self.source_content, re.DOTALL)
        if main_match:
            main_body = main_match.group(1)
            for pattern in call_patterns:
                matches = re.finditer(pattern, main_body)
                for match in matches:
                    value = int(match.group(1))
                    logger.debug(f"Found call in main: {func_name}({value})")
                    return value
        
        return None

    def analyze_recursion_depth(self, recursive_functions):
        """Rekursijas dziļuma aprēķins ar parametru sekošanu cauri funkciju izsaukumiem"""
        recursion_limits = {}
        reduction_info = {}
        
        for func in recursive_functions:
            if not self.source_content:
                raise RuntimeError(f"Cannot determine recursion depth for function '{func}': Source code not available for analysis")
            
            logger.info(f"Analyzing recursion depth for {func}")
            
            # 1. metode: Meklē tiešos izsaukumus ar literāļu skaitļiem
            direct_literal_patterns = [
                rf'{re.escape(func)}\s*\(\s*(\d+)\s*\)',
                rf'{re.escape(func)}\(\s*(\d+)\s*\)'
            ]
            
            initial_value = None
            found_initial_value = False
            
            for pattern in direct_literal_patterns:
                matches = re.finditer(pattern, self.source_content, re.IGNORECASE)
                for match in matches:
                    value = int(match.group(1))
                    logger.debug(f"Found direct literal call: {func}({value})")
                    initial_value = value
                    found_initial_value = True
                    # Ņem lielāko vērtību, ja atrasti vairāki izsaukumi
                    if initial_value and value > initial_value:
                        initial_value = value
            
            # 2. metode: Meklē mainīgo piešķīrumus un pēc tam izsaukumus main funkcijā
            if not found_initial_value:
                main_func_match = re.search(r'int\s+main\s*\([^)]*\)\s*{([^}]*(?:{[^}]*}[^}]*)*)}', 
                                            self.source_content, re.DOTALL)
                if main_func_match:
                    main_body = main_func_match.group(1)
                    
                    # Atrod izsaukumu uz mūsu funkciju main funkcijā
                    call_match = re.search(rf'{re.escape(func)}\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)', main_body)
                    if call_match:
                        var_name = call_match.group(1)
                        logger.debug(f"Found call with variable: {func}({var_name})")
                        
                        # Meklē mainīgā piešķīrumu main funkcijā
                        var_patterns = [
                            rf'(?:int\s+|uint\d+_t\s+)?{re.escape(var_name)}\s*=\s*(\d+)',
                            rf'{re.escape(var_name)}\s*=\s*(\d+)'
                        ]
                        
                        for pattern in var_patterns:
                            var_match = re.search(pattern, main_body)
                            if var_match:
                                initial_value = int(var_match.group(1))
                                logger.debug(f"Found variable assignment: {var_name} = {initial_value}")
                                found_initial_value = True
                                break
            
            # 3. metode: Izseko parametru vērtības caur funkciju izsaukumiem
            if not found_initial_value:
                initial_value = self.trace_parameter_through_calls(func)
                if initial_value is not None:
                    found_initial_value = True
                    logger.debug(f"Found value through parameter tracing: {initial_value}")
            
            # 4. metode: Meklē šablonus funkcijas definīcijā
            if not found_initial_value:
                # Mēģina atrast tiešos izsaukumus citās funkcijās
                all_calls = re.finditer(rf'{re.escape(func)}\s*\(\s*(\d+)\s*\)', self.source_content)
                for match in all_calls:
                    value = int(match.group(1))
                    if not initial_value or value > initial_value:
                        initial_value = value
                        found_initial_value = True
                        logger.debug(f"Found function call with literal: {func}({value})")
            
            # Ja rekursijas dziļums nav nosakāms, izmet kļūdu
            if not found_initial_value or initial_value is None:
                raise RuntimeError(
                    f"Cannot determine recursion depth for function '{func}':"
                    f"Unable to find initial parameter value."
                )

            # Nosaka rekursijas tipu balstoties uz funkcijas šablonu
            recursion_type, reduction_factor = self.detect_recursion_type(func)

            if recursion_type == "countdown":
                # Atskaitīšanas rekursijai (n, n-samazināšanas_faktors, n-2*samazināšanas_faktors, ..., 0)
                # Aprēķina cik soļu nepieciešams, lai sasniegtu 0
                recursion_limits[func] = (initial_value // reduction_factor) + 1
                reduction_info[func] = {"type": "subtraction", "value": reduction_factor}
                logger.info(f"Detected countdown recursion for {func}")
                logger.info(f"  Initial value: {initial_value}")
                logger.info(f"  Reduction factor: {reduction_factor}")
                logger.info(f"  Total recursion calls: {recursion_limits[func]}")
            elif recursion_type == "dividing":
                # Dalīšanas rekursijai (n, n/samazināšanas_faktors, n/samazināšanas_faktors^2, ..., 1)
                import math
                recursion_limits[func] = math.ceil(math.log(initial_value, reduction_factor)) + 1
                reduction_info[func] = {"type": "division", "value": reduction_factor}
                logger.info(f"Detected dividing recursion for {func}")
                logger.info(f"  Initial value: {initial_value}")
                logger.info(f"  Divisor: {reduction_factor}")
                logger.info(f"  Total recursion calls: {recursion_limits[func]}")
            else:
                # Noklusējums: pieņem atskaitīšanu ar samazināšanas faktoru 1
                recursion_limits[func] = initial_value + 1
                reduction_info[func] = {"type": "unknown", "value": 1}
                logger.warning(f"Unknown recursion type for {func}, assuming countdown with step 1")
        
        return recursion_limits, reduction_info

    def detect_recursion_type(self, func_name):
        """Nosaka rekursijas veidu - atskaitīšana vai dalīšana"""
        if not self.source_content:
            return "unknown", 1
        
        # Atrod funkcijas definīciju
        func_pattern = rf'{re.escape(func_name)}\s*\([^)]*\)\s*{{([^{{}}]*(?:{{[^{{}}]*}}[^{{}}]*)*)}}'
        func_match = re.search(func_pattern, self.source_content, re.DOTALL)
        
        if not func_match:
            return "unknown", 1
        
        func_body = func_match.group(1)
        
        # Pārbauda (x - N) šablonu (atskaitīšana)
        countdown_match = re.search(rf'{re.escape(func_name)}\s*\([^)]*-\s*(\d+)[^)]*\)', func_body)
        if countdown_match:
            reduction = int(countdown_match.group(1))
            return "countdown", reduction
        
        # Pārbauda (x / N) šablonu (dalīšana ar N)
        division_match = re.search(rf'{re.escape(func_name)}\s*\([^)]*\/\s*(\d+)[^)]*\)', func_body)
        if division_match:
            divisor = int(division_match.group(1))
            return "dividing", divisor
        
        # Pārbauda (x >> N) šablonu (dalīšana ar 2^N, izmantojot bitu nobīdi)
        bitshift_match = re.search(rf'{re.escape(func_name)}\s*\([^)]*>>\s*(\d+)[^)]*\)', func_body)
        if bitshift_match:
            shift_amount = int(bitshift_match.group(1))
            divisor = 2 ** shift_amount
            return "dividing", divisor
        
        return "unknown", 1

    def build_call_graph(self, asm_code, gcc_stack_usage):
        """Izsaukumu grafa veidošana ar atbalstu optimizētajām funkcijām un netiešajiem izsaukumiem"""
        logger.info("Building call graph from assembly instructions...")
        
        # Funkciju adrešu kartējums - gan baitu, gan vārdu adreses
        function_addresses = {}
        func_pattern = re.compile(r'^([0-9a-f]+) <([^>]+)>:')
        
        # Atrod funkciju adreses
        for line in asm_code.split('\n'):
            match = func_pattern.match(line)
            if match:
                addr_str, func_name = match.groups()
                
                # Izlaiž, ja nav mūsu steka izmantojuma ierakstos
                if func_name.startswith('__') or func_name.startswith('.'):
                    continue
                    
                byte_addr = int(addr_str, 16)
                word_addr = byte_addr // 2  # AVR izsaukums izmanto vārdu adreses
                
                # Glabā vairākus adrešu formātus
                for addr_format in [
                    addr_str,                    # Oriģinālais formāts: "00000112"
                    addr_str.lstrip('0') or '0', # Bez nullēm: "112" 
                    f"{byte_addr:x}",            # Hex bez nullēm: "112"
                    f"{word_addr:x}",            # Vārda adrese: "89"
                    f"{word_addr:x}".lstrip('0') or '0'  # Vārda adrese bez nullēm: "89"
                ]:
                    function_addresses[addr_format] = func_name
                
                logger.debug(f"Mapping {func_name} at {addr_str} (byte addr: 0x{byte_addr:x}, word addr: 0x{word_addr:x})")
        
        # Inicializē izsaukuma grafu bāzes funkcijām
        call_graph = {}
        for func in gcc_stack_usage.keys():
            call_graph[func] = []
        
        avr_call_pattern = re.compile(r'^\s*([0-9a-f]+):\s+[0-9a-f ]+\s+(?:call|rcall)\s+(?:0x)?([0-9a-f]+)')
        rcall_relative_pattern = re.compile(r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+rcall\s+\.([+-]\d+)')
        indirect_call_pattern = re.compile(r'^\s*([0-9a-f]+):\s+[0-9a-f ]+\s+(?:icall|eicall)\s*')
        
        # Z reģistra (r30/r31) izsekošanas šabloni
        ldi_r30_pattern = re.compile(r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+ldi\s+r30,\s+(?:lo8\(.*\)|\s*0x)?([0-9a-f]+)(?:\)?)?')
        ldi_r31_pattern = re.compile(r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+ldi\s+r31,\s+(?:hi8\(.*\)|\s*0x)?([0-9a-f]+)(?:\)?)?')
        
        # Masīva piekļuves šabloni
        array_access_pattern = re.compile(r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+(?:ld|ldd)\s+(?:r\d+,\s+(?:Z|Y)|(?:Z|Y)\+\d)')
        
        current_function = None
        
        # Izseko Z reģistra stāvokli katrai funkcijai
        r30_values = {}
        r31_values = {}
        z_targets = {}
        
        array_access_detected = False
        
        # Apstrādā assemblera rinda pēc rindas
        for line in asm_code.split('\n'):
            # Pārbauda funkcijas definīciju
            func_match = func_pattern.match(line)
            if func_match:
                addr_str, func_name = func_match.groups()
                
                # Izlaiž kompilatora ģenerētās atzīmes
                if '^' in func_name or func_name.startswith('.L') or func_name.startswith('.Loc'):
                    if current_function:
                        logger.debug(f"Ignoring compiler-generated label: {func_name}, staying in {current_function}")
                    continue
                
                # Pārbauda, vai šī ir funkcija, ko mēs izsekojam
                if func_name in gcc_stack_usage:
                    current_function = func_name
                    logger.debug(f"Entering function: {current_function} (from {func_name})")
                    
                    # Inicializē izsekošanu šai funkcijai, ja nepieciešams
                    if current_function not in r30_values:
                        r30_values[current_function] = None
                        r31_values[current_function] = None
                        z_targets[current_function] = []
                continue
            
            if not current_function:
                continue
            
            # Tiešā izsaukuma noteikšana
            call_match = avr_call_pattern.match(line)
            if call_match:
                instr_addr, call_addr = call_match.groups()
                called_func = None

                # Mēģina dažādus adrešu formātus meklēšanai
                if call_addr in function_addresses:
                    called_func = function_addresses[call_addr]
                else:
                    normalized_addr = call_addr.lstrip('0') or '0'
                    if normalized_addr in function_addresses:
                        called_func = function_addresses[normalized_addr]
                
                if called_func and called_func not in call_graph[current_function]:
                    call_graph[current_function].append(called_func)
                    logger.info(f"Found call from {current_function} to {called_func}")
                    logger.debug(f"  Call instruction: {line.strip()}")
                else:
                    logger.debug(f"Call to unresolved address {call_addr} in {current_function}")
                continue
            
            # Izseko vērtību ielādi Z reģistrā
            ldi_r30_match = ldi_r30_pattern.search(line)
            if ldi_r30_match:
                r30_values[current_function] = ldi_r30_match.group(1)
                logger.debug(f"Loaded r30 with 0x{r30_values[current_function]} in {current_function}")
                continue
            
            ldi_r31_match = ldi_r31_pattern.search(line)
            if ldi_r31_match:
                r31_values[current_function] = ldi_r31_match.group(1)
                logger.debug(f"Loaded r31 with 0x{r31_values[current_function]} in {current_function}")
                continue
            
            # Atklāj masīva piekļuvi funkciju rādītājiem
            if array_access_pattern.search(line):
                array_access_detected = True
                logger.debug(f"Detected potential function pointer array load in {current_function}")
                continue
            
            # Relatīvs rcall (izmantots inline assemblers)
            rcall_match = rcall_relative_pattern.match(line)
            if rcall_match:
                offset = rcall_match.group(1)
                if offset == "+0":
                    # Ignorē rcall .+0 - steka ietvara uzstādīšanas triks
                    logger.debug(f"Found stack frame setup via rcall .+0 in {current_function}")
                    continue
                
                # Meklē funkciju nosaukumus tieši assemblera rindā inline assembleram
                for func_name in gcc_stack_usage.keys():
                    if func_name in line:
                        if func_name not in call_graph[current_function]:
                            call_graph[current_function].append(func_name)
                            logger.info(f"Found relative rcall from {current_function} to {func_name}")
                        break
                else:
                    logger.debug(f"Relative call with offset {offset} in {current_function} - target unknown")
                continue
            
            # Apstrādā icall/eicall
            icall_match = indirect_call_pattern.match(line)
            if icall_match:
                instr_addr = icall_match.group(1)
                logger.debug(f"Found icall at 0x{instr_addr} in {current_function}")
                
                # 1. gadījums: Z reģistrs ir ielādēts ar tiešu adresi
                if r30_values[current_function] is not None and r31_values[current_function] is not None:
                    # Apvieno r31:r30, lai izveidotu pilnu adresi (little endian)
                    r30_val = r30_values[current_function].lstrip('0') or '0'
                    r31_val = r31_values[current_function].lstrip('0') or '0'
                    
                    # Vairāki veidi, kā veidot adreses
                    addr_formats = [
                        # Tiešais savienojums
                        r31_val + r30_val,
                        
                        # Ar padding
                        f"{int(r31_val, 16):02x}{int(r30_val, 16):02x}",
                        
                        # Tikai apakšējie baiti (r30)
                        r30_val,
                        
                        # Tiešā Z reģistra vērtība (baitu adrese)
                        f"{(int(r31_val, 16) << 8 | int(r30_val, 16)):x}",
                        
                        # Vārda adrese (Z reģistra vērtība ÷ 2)  
                        f"{(int(r31_val, 16) << 8 | int(r30_val, 16)) // 2:x}",
                    ]
                    
                    # Noņem dublikātus un pārbauda katru formātu
                    addr_formats = list(set(addr_formats))
                    
                    matched = False
                    for addr_format in addr_formats:
                        if addr_format in function_addresses:
                            target_func = function_addresses[addr_format]
                            if target_func not in call_graph[current_function]:
                                call_graph[current_function].append(target_func)
                                logger.info(f"Resolved icall in {current_function} to {target_func} (addr: 0x{addr_format})")
                                logger.debug(f"  Z register: r31=0x{r31_val}, r30=0x{r30_val}")
                                matched = True
                                break
                    
                    if not matched:
                        logger.warning(f"Could not resolve icall target in {current_function}")
                        logger.debug(f"  Z register: r31=0x{r31_val}, r30=0x{r30_val}")
                        logger.debug(f"  Tried addresses: {addr_formats}")
                        logger.debug(f"  Available functions: {list(function_addresses.keys())}")
                    
                    # Atiestate Z reģistra izsekošanu pēc icall
                    r30_values[current_function] = None
                    r31_values[current_function] = None
                
                # 2. gadījums: Masīva bāzēti funkciju rādītāju izsaukumi
                elif array_access_detected:
                    # Pievieno visas ne-main, ne-pašreizējās funkcijas kā iespējamos mērķus
                    potential_targets = []
                    for func_name in gcc_stack_usage.keys():
                        # Izslēdz main (parasti nav funkciju masīvā)
                        # Izslēdz pašreizējo funkciju (lai izvairītos no bezgalīguma)
                        # Izslēdz utility funkcijas
                        exclude_funcs = {'main', current_function}
                        utility_funcs = {'delay_ms', 'delay_us', '_delay_ms', '_delay_us'}
                        exclude_funcs.update(utility_funcs)
                        
                        if func_name not in exclude_funcs:
                            potential_targets.append(func_name)
                    
                    # Pievieno visus potenciālos mērķus
                    for target_func in potential_targets:
                        if target_func not in call_graph[current_function]:
                            call_graph[current_function].append(target_func)
                            logger.info(f"Added potential icall target {target_func} to {current_function} (array-based)")
                    
                    array_access_detected = False
                    
                # 3. gadījums: Nezināms netiešais izsaukums
                else:
                    logger.warning(f"Indirect call without Z register tracking or array access in {current_function}")
                
                continue
        
        # Veic papildu pārbaudes priekš neizrisināto netiešo izsaukumu        
        # Meklē funkcijas, kurās ir icall, bet nav atrisināti mērķi
        for func_name, callees in call_graph.items():
            # Pārbauda, vai funkcijā ir icall instrukcijas
            func_asm_start = None
            func_asm_end = None
            
            # Atrod funkcijas assemblera kodu
            func_pattern = re.compile(rf'^([0-9a-f]+) <{re.escape(func_name)}>:')
            lines = asm_code.split('\n')
            
            for i, line in enumerate(lines):
                if func_pattern.match(line):
                    func_asm_start = i
                    # Atrod nākamo funkciju vai šīs funkcijas beigas
                    for j in range(i + 1, len(lines)):
                        if re.match(r'^[0-9a-f]+ <[^>]+>:', lines[j]):
                            func_asm_end = j
                            break
                    else:
                        func_asm_end = len(lines)
                    break
            
            if func_asm_start is not None and func_asm_end is not None:
                func_asm = '\n'.join(lines[func_asm_start:func_asm_end])
                
                # Pārbauda icall eksistenci
                if re.search(r'icall|eicall', func_asm):
                    if not callees:
                        logger.warning(f"Function {func_name} has indirect calls but no resolved targets")
                        
        return call_graph

    def analyze_static_stack_usage(self, asm_code, gcc_stack_usage):
        """Analizē maksimālo steka izmantojumu, balstoties uz disasambleto kodu."""
        logger.info("Static Analysis: Analyzing stack operations...")
        
        # Rekursijas noteikšana izmantojot bāzes funkciju nosaukumus
        recursive_functions = self.detect_recursion_from_assembly(asm_code, gcc_stack_usage)
        
        # Rekursijas dziļuma novērtējums
        recursion_limits, reduction_info = self.analyze_recursion_depth(recursive_functions)
        
        # Izsaukuma grafa noteikšana
        call_graph = self.build_call_graph(asm_code, gcc_stack_usage)
        
        # Aprēķina steka izmantojumu no assemblera koda
        calculated_stack_usage = self.analyze_function_stack_usage_from_asm(asm_code)
        
        # Funkciju analīze
        function_stack_usage = {}
        
        for function_name in gcc_stack_usage.keys():
            # Ja funkcijas ir aprēķinātas no assemblera, izmanto tās
            if function_name in calculated_stack_usage:
                function_stack_usage[function_name] = calculated_stack_usage[function_name]
                logger.debug(f"Function {function_name}: using calculated value {calculated_stack_usage[function_name]} bytes")
            else:
                # Ja ne, izmanto GCC vērtību, ja tāda ir
                gcc_value = gcc_stack_usage.get(function_name, 0)
                if gcc_value > 0:
                    function_stack_usage[function_name] = gcc_value
                    logger.debug(f"Function {function_name}: using GCC value {gcc_value} bytes")
                else:
                    raise RuntimeError(
                        f"Cannot determine stack usage for function '{function_name}': "
                        f"Function not found in calculated stack usage or GCC stack usage reports. "
                    )
        
        # Pievieno mapping starp assemblera un GCC funkciju nosaukumiem
        asm_to_gcc_mapping = {}
        
        # Apkopo visas assemblera funkcijas no call_graph (gan keys, gan values)
        all_asm_functions = set(call_graph.keys())
        for callees in call_graph.values():
            all_asm_functions.update(callees)

        # Meklē mappings
        for asm_func in all_asm_functions:
            for gcc_func in gcc_stack_usage.keys():
                # Ja assemblera funkcija sākas ar GCC funkcijas nosaukumu
                if asm_func.startswith(gcc_func):
                    asm_to_gcc_mapping[asm_func] = gcc_func
                    break

        # Papildina function_stack_usage ar assemblera funkcijām
        for asm_func, gcc_func in asm_to_gcc_mapping.items():
            if asm_func not in function_stack_usage:
                function_stack_usage[asm_func] = gcc_stack_usage[gcc_func]
                logger.debug(f"Mapped {asm_func} -> {gcc_func}: {gcc_stack_usage[gcc_func]} bytes")

        # Pievieno rekursīvos pašizsaukumus izsaukumu grafam
        for func in recursive_functions:
            if func not in call_graph:
                call_graph[func] = []
            if func not in call_graph[func]:
                call_graph[func].append(func)
                logger.info(f"Added self-call for recursive function {func}")
        
        # Izveido pilnu izsaukumu grafu
        complete_call_graph = {func: callees.copy() for func, callees in call_graph.items()}
        
        logger.info(f"Detected recursive functions: {recursive_functions}")
        logger.info(f"Recursion limits: {recursion_limits}")
        logger.info(f"Final call graph: {complete_call_graph}")
        
        # Aprēķina maksimālo steka izmantojumu
        max_stack_usage, all_complete_paths = self.calculate_max_stack_usage(
            function_stack_usage, 
            complete_call_graph, 
            recursive_functions, 
            recursion_limits
        )
        
        # Pievieno drošības rezervi 10%
        safe_max_stack_usage = int(max_stack_usage * 1.10)
        
        analysis_results = {
            'max_stack_usage': safe_max_stack_usage,
            'raw_max_usage': max_stack_usage,
            'function_usage': function_stack_usage,
            'call_graph': complete_call_graph,
            'recursive_functions': list(recursive_functions),
            'recursion_limits': recursion_limits,
            'reduction_info': dict(reduction_info),
            'all_paths': all_complete_paths
        }
        
        return analysis_results

    def analyze_function_stack_usage_from_asm(self, asm_code):
        """
        Analizē AVR assemblera kodu, lai aprēķinātu steka izmantojumu katrai funkcijai,
        balstoties uz PUSH/POP instrukcijām un steka rādītāja korekcijām.
        """
        function_stack_usage = {}
        
        # Funkciju meklēšanas šablons assemblera izdrukā
        func_pattern = re.compile(r'^([0-9a-f]+) <([^>]+)>:')
        
        # Y reģistra steka rāmja šabloni
        sbiw_pattern = re.compile(r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+sbiw\s+r28,\s+0x([0-9a-f]+)')
        adiw_pattern = re.compile(r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+adiw\s+r28,\s+0x([0-9a-f]+)')
        
        # SPL/SPH tiešās manipulācijas šabloni
        spl_in_pattern = re.compile(r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+in\s+r\d+,\s*0x3d')
        sph_in_pattern = re.compile(r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+in\s+r\d+,\s*0x3e')
        spl_out_pattern = re.compile(r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+out\s+0x3d,\s*r\d+')
        sph_out_pattern = re.compile(r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+out\s+0x3e,\s*r\d+')
        
        # Funkciju izsaukumu šablon
        call_pattern = re.compile(r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+(?:call)\s+')
        rcall_pattern = re.compile(r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+(?:rcall)\s+')
        rcall_relative_pattern = re.compile(r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+rcall\s+\.([+-]\d+)')
        icall_pattern = re.compile(r'^\s*[0-9a-f]+:\s+[0-9a-f ]+\s+(?:icall|eicall)\s*')
        
        # Funkciju meklēšana un assemblera koda sadalīšana pa funkcijām
        current_function = None
        func_start = None
        functions = {}
        
        lines = asm_code.split('\n')
        
        # Ignorē kompilatora ģenerētās atzīmes
        ignore_labels = set()
        
        for i, line in enumerate(lines):
            match = func_pattern.match(line)
            if match:
                func_addr = match.group(1)
                func_name = match.group(2)
                
                #  Ignorē kompilatora ģenerētās atzīmes
                if '^' in func_name or func_name.startswith('.L') or func_name.startswith('.Loc'):
                    if current_function:
                        # Šī ir atzīme pašreizējās funkcijas ietvaros, nevis jauna funkcija
                        if func_name not in ignore_labels:
                            ignore_labels.add(func_name)
                            logger.debug(f"Ignoring compiler-generated label: {func_name}")
                    continue
                
                # Saglabā iepriekšējo funkciju
                if current_function and current_function not in ignore_labels:
                    functions[current_function] = {
                        'start': func_start,
                        'end': i - 1,
                        'addr': func_addr
                    }
                
                # Sāk jaunu funkciju
                current_function = func_name
                func_start = i
        
        # Pievieno pēdējo funkciju
        if current_function and current_function not in ignore_labels:
            functions[current_function] = {
                'start': func_start,
                'end': len(lines) - 1,
                'addr': func_addr
            }
        
        # Analizē katru funkciju
        for func_name, func_info in functions.items():
            
            # Izlaiž sistēmas/kompilatora ģenerētās funkcijas
            if func_name.startswith('__') or func_name in ('__ctors_end', '__bad_interrupt', '_exit', '__stop_program'):
                continue
            
            # Funkcijas assemblera kods
            func_lines = lines[func_info['start']:func_info['end']+1]
            
            # Skaita steka izmantojumu
            push_count = 0
            pop_count = 0
            stack_adjust_down = 0  # Steka palielināšana (SBIW)
            stack_adjust_up = 0    # Steka samazināšana (ADIW)
            
            # Skaita dažādu tipu izsaukumus
            call_count = 0
            rcall_count = 0
            icall_count = 0
            
            # SPL/SPH manipulācijas skaitītāji
            spl_manipulations = 0
            sph_manipulations = 0
            
            # Pilna funkcijas analīze
            for line in func_lines:
                # Atrod PUSH instrukcijas (palielina steku)
                if "push" in line and "r" in line:
                    push_count += 1
                
                # Atrod POP instrukcijas (samazina steku)
                if "pop" in line and "r" in line:
                    pop_count += 1
                
                # Atrod steka rāmja uzstādīšanu (SBIW r28,X) - palielina steku
                sbiw_match = sbiw_pattern.search(line)
                if sbiw_match:
                    adj_value = int(sbiw_match.group(1), 16)
                    stack_adjust_down += adj_value
                
                # Atrod steka rāmja noņemšanu (ADIW r28,X) - samazina steku
                adiw_match = adiw_pattern.search(line)
                if adiw_match:
                    adj_value = int(adiw_match.group(1), 16)
                    stack_adjust_up += adj_value

                # Pārbauda SPL/SPH manipulācijas
                if spl_in_pattern.search(line) or spl_out_pattern.search(line):
                    spl_manipulations += 1
                    logger.debug(f"SPL manipulation detected in {func_name}: {line.strip()}")
                
                if sph_in_pattern.search(line) or sph_out_pattern.search(line):
                    sph_manipulations += 1
                    logger.debug(f"SPH manipulation detected in {func_name}: {line.strip()}")

                # Skaita call instrukcijas
                if call_pattern.search(line):
                    call_count += 1
                
                # Skaita rcall instrukcijas (izņemot .+0)
                if rcall_pattern.search(line):
                    rel_match = rcall_relative_pattern.search(line)
                    if rel_match:
                        offset = rel_match.group(1)
                        if offset == "+0":
                            # rcall .+0 rezervē 2 baitus stekā
                            stack_adjust_down += 2  
                            logger.debug(f"Found rcall .+0 pattern, adding 2 bytes to stack")
                        else:
                            # Parasts rcall ar nobīdi - funkcijas izsaukums
                            rcall_count += 1
                    else:
                        # rcall ar adresi
                        rcall_count += 1
                
                # Skaita icall/eicall instrukcijas
                if icall_pattern.search(line):
                    icall_count += 1
            
            # Pārbauda, vai ir kādas Y reģistra steka manipulācijas
            has_y_register_stack_frame = stack_adjust_down > 0
            
            # Pārbaude par steka bilanci
            if push_count != pop_count:
                logger.debug(f"Function {func_name} has unbalanced PUSH/POP: {push_count} pushes, {pop_count} pops")
            
            if stack_adjust_down != stack_adjust_up:
                logger.debug(f"Function {func_name} has unbalanced stack adjustments: down {stack_adjust_down}, up {stack_adjust_up}")
                                
            # Steka izmantojums funkcijas izsaukumiem (CALL, RCALL, ICALL)
            # Katrs izsaukums aizņem 2 baitus atgriešanās adresei
            return_addr_size = 2  # AVR atgriešanās adrese ir 2 baiti
            
            # Kopējais maksimālais steka izmantojums
            # PUSH instrukcijas + steka rāmis + atgriešanās adrese 
            # (POP un ADIW mūs neinteresē, jo tie tikai samazina steku)
            total_stack = push_count + stack_adjust_down + return_addr_size

            # Izmet brīdinājumu par SPL/SPH manipulācijām tikai tad, ja nav Y reģistra steka rāmja
            if (spl_manipulations > 0 or sph_manipulations > 0) and not has_y_register_stack_frame:
                logger.warning(f"Function '{func_name}' uses direct stack pointer manipulation "
                            f"(SPL: {spl_manipulations}, SPH: {sph_manipulations} operations) "
                            f"instead of standard Y register frame. Stack usage analysis may be "
                            f"incomplete - actual usage might differ from calculated {total_stack} bytes.")
            
            # Ieraksta rezultātu
            function_stack_usage[func_name] = total_stack
            
            logger.debug(f"ASM stack analysis for {func_name}: push={push_count}, pop={pop_count}, " + 
                        f"frame_down={stack_adjust_down}, frame_up={stack_adjust_up}, " + 
                        f"call={call_count}, rcall={rcall_count}, icall={icall_count}, " +
                        f"spl_ops={spl_manipulations}, sph_ops={sph_manipulations}, " +
                        f"return={return_addr_size}, total={total_stack}")
        
        return function_stack_usage

    def calculate_max_stack_usage(self, function_stack_usage, call_graph, recursive_functions, recursion_limits):
        """
        Aprēķina maksimālo steka izmantojumu, analizējot visus izsaukumu ceļus.
        Algoritms rekursīvi iziet cauri call graph, aprēķina katru ceļu un atrod maksimālo stack usage.
        Īpaši apstrādā rekursīvās funkcijas, izmantojot iepriekš aprēķinātus rekursijas dziļumus.
        """
        logger.info("Calculating maximum stack usage...")
        
        # Pārbauda vai visām rekursīvām funkcijām ir noteikts rekursijas ierobežojums
        for func in recursive_functions:
            if func not in recursion_limits:
                raise RuntimeError(
                    f"Recursion depth not determined for function '{func}'."
                    f"Cannot proceed with stack analysis."
                )

        # Iepriekš aprēķina rekursīvo steka izmantojumu
        recursive_stack = {}
        for func in recursive_functions:
            # Iegūst vietējo steka izmantojumu šai funkcijai
            local_usage = function_stack_usage.get(func, 0)

            # Iegūst rekursijas dziļumu
            depth = recursion_limits[func]
            
            # Kopējais rekursīvais steks šai funkcijai
            total = local_usage * depth
            recursive_stack[func] = total
            
            logger.info(f"Recursive function {func}: depth {depth}, local {local_usage}, total recursive {total}")
        
        # Izseko visus pilnus ceļus
        all_complete_paths = []
        max_path = []
        max_usage = 0
        
        # Izveido memoizācijas kešu apmeklētajiem ceļiem, lai izvairītos no pārrēķināšanas
        memo = {}
        
        def get_stack_usage(func_name, call_path=None, depth=0):
            nonlocal max_path, max_usage, all_complete_paths 
            """Rekursīvi aprēķina steka lietojumu, izmantojot izsaukumu grafu."""

            if call_path is None:
                call_path = []
            
            # Generē kešēšanas atslēgu
            cache_key = (func_name, tuple(call_path))
            if cache_key in memo:
                return memo[cache_key]
            
            # Funkcija nav atrasta mūsu analīzē
            if func_name not in function_stack_usage:
                logger.warning(f"{'  ' * depth}Function {func_name} not found in analysis")
                return 0
            
            # Iegūst vietējo steka izmantojumu šai funkcijai
            local_usage = function_stack_usage[func_name]
            current_path = call_path + [func_name]
            is_root_call = len(call_path) == 0
            
            # Debug: Rāda pašreizējo ceļu
            path_str = " -> ".join(current_path)
            logger.debug(f"{'  ' * depth}Analyzing path: {path_str}")
            logger.debug(f"{'  ' * depth}{func_name}: local usage {local_usage}")
            
            # Iegūst visus iespējamos ceļus no šīs funkcijas
            called_functions = call_graph.get(func_name, [])
            
            # Īpaša apstrāde rekursīvām funkcijām
            if func_name in recursive_functions:
                # Ja šis ir pirmais izsaukums uz rekursīvu funkciju ceļā
                if func_name not in call_path:
                    # Paplašina rekursīvos izsaukumus ceļā
                    recursion_limit = recursion_limits[func_name]
                    expanded_path = current_path.copy()
                    
                    # Pievieno rekursīvos izsaukumus ceļam
                    for i in range(1, recursion_limit):
                        expanded_path.append(func_name)
                    
                    # Aprēķina kopējo izmantojumu pilnam rekursīvam ceļam
                    path_total = sum(function_stack_usage.get(func, 0) for func in expanded_path)
                    all_complete_paths.append({
                        'path': expanded_path.copy(),
                        'usage': path_total,
                        'details': f"{' -> '.join(expanded_path)}: {path_total} bytes"
                    })
                    
                    # Atgriež pilno rekursīvo steka izmantojumu
                    memo[cache_key] = recursive_stack[func_name]
                    return recursive_stack[func_name]
                else:
                    # Novērš bezgalīgas cilpas - jau esam rekursīvā izsaukumā
                    logger.debug(f"{'  ' * depth}Already in recursive path, returning 0")
                    return 0
            
            # Pārbauda parastās cilpas (ne-rekursīvas)
            if func_name in call_path:
                logger.debug(f"{'  ' * depth}Already in path, returning 0")
                return 0
            
            # Noņem rekursīvos pašizsaukumus no izsaukumu saraksta, apstrādājot pirmo sastapšanas reizi
            filtered_calls = []
            for called_func in called_functions:
                if called_func == func_name and func_name in recursive_functions:
                    continue  # Izlaiž pašizsaukumus rekursīvām funkcijām
                filtered_calls.append(called_func)
            
            # Ja šī ir lapas funkcija (bez izsaukumiem), ieraksta ceļu
            if not filtered_calls:
                path_total = sum(function_stack_usage.get(func, 0) for func in current_path)
                all_complete_paths.append({
                    'path': current_path.copy(),
                    'usage': path_total,
                    'details': f"{path_str}: {path_total} bytes"
                })
                memo[cache_key] = local_usage
                return local_usage
            
            # Aprēķina maksimālo izsaukto steku
            max_call_stack = 0
            
            for called_func in filtered_calls:
                called_stack = get_stack_usage(called_func, current_path, depth + 1)
                
                logger.debug(f"{'  ' * depth}  Call to {called_func}: {called_stack}")
                
                if called_stack > max_call_stack:
                    max_call_stack = called_stack
            
            # Kopējais izmantojums ir vietējais izmantojums + maksimālais izsaukuma steks
            total_usage = local_usage + max_call_stack
            logger.debug(f"{'  ' * depth}{func_name}: total usage = {local_usage} + {max_call_stack} = {total_usage}")
            
            # Izseko maksimālo ceļu no saknes
            if is_root_call and total_usage > max_usage:
                max_usage = total_usage
                max_path = self.find_max_stack_path(func_name, call_graph, function_stack_usage, recursive_functions, recursion_limits)
            
            # Pieraksta memoizācijas kešā
            memo[cache_key] = total_usage
            return total_usage
        
        # Aprēķina no main
        result = get_stack_usage('main')
        
        # Noņem dublikātus un kārto ceļus pēc izmantojuma
        unique_paths = {}
        for path_info in all_complete_paths:
            path_key = " -> ".join(path_info['path'])
            if path_key not in unique_paths or path_info['usage'] > unique_paths[path_key]['usage']:
                unique_paths[path_key] = path_info
        
        all_complete_paths = list(unique_paths.values())
        all_complete_paths.sort(key=lambda x: x['usage'], reverse=True)
        
        # Ziņo par visiem atrastajiem ceļiem
        logger.info("\n" + "="*50)
        logger.info("ALL STACK PATHS ANALYZED:")
        logger.info("="*50)
        
        for i, path_info in enumerate(all_complete_paths):
            logger.info(f"{i+1:2d}. {path_info['details']}")
        
        # Iegūst pilno maksimālo ceļu no main
        complete_max_path = self.find_max_stack_path('main', call_graph, function_stack_usage, recursive_functions, recursion_limits)
        total_max_usage = sum(function_stack_usage.get(func, 0) for func in complete_max_path)
        
        logger.info("\n" + "="*50)
        logger.info("MAXIMUM STACK PATH:")
        logger.info("="*50)
        max_path_str = " -> ".join(complete_max_path)
        logger.info(f"Path: {max_path_str}")
        logger.info(f"Total Usage: {total_max_usage} bytes")
        
        # Rāda soli pa solim aprēķinu maksimālajam ceļam
        logger.info("\nStep-by-step calculation:")
        logger.info("-" * 30)
        current_total = 0
        for i, func in enumerate(complete_max_path):
            if i == 0:
                local = function_stack_usage.get(func, 0)
                current_total += local
                logger.info(f"{func}: {local} bytes (entry point, includes own return addr)")
            else:
                local = function_stack_usage.get(func, 0)
                current_total += local
                logger.info(f"{func}: {local} bytes (includes return addr)")
                logger.info(f"  Running total: {current_total} bytes")
        
        return result, all_complete_paths

    def find_max_stack_path(self, start_func, call_graph, function_stack_usage, recursive_functions=None, recursion_limits=None):
        """Atrod pilno ceļu ar maksimālo steka izmantojumu, ieskaitot rekursijas"""
        if recursive_functions is None:
            recursive_functions = set()
        if recursion_limits is None:
            recursion_limits = {}
        
        def find_max_branch(current_func, visited=None):
            if visited is None:
                visited = set()
            
            if current_func in visited:
                return [current_func], function_stack_usage.get(current_func, 0)
            
            visited.add(current_func)
            
            # Apstrādā rekursīvas funkcijas
            if current_func in recursive_functions:
                recursion_limit = recursion_limits.get(current_func, 4)
                expanded_path = [current_func] * recursion_limit
                total_usage = sum(function_stack_usage.get(func, 0) for func in expanded_path)
                visited.remove(current_func)
                return expanded_path, total_usage
            
            if current_func not in call_graph or not call_graph[current_func]:
                visited.remove(current_func)
                return [current_func], function_stack_usage.get(current_func, 0)
            
            max_path = [current_func]
            max_usage = function_stack_usage.get(current_func, 0)
            
            # Filtrē pašizsaukumus rekursīvām funkcijām
            filtered_calls = []
            for called_func in call_graph[current_func]:
                if called_func == current_func and current_func in recursive_functions:
                    continue
                filtered_calls.append(called_func)
            
            for called_func in filtered_calls:
                sub_path, sub_usage = find_max_branch(called_func, visited.copy())
                total_usage = function_stack_usage.get(current_func, 0) + 2 + sub_usage
                
                if total_usage > max_usage:
                    max_path = [current_func] + sub_path
                    max_usage = total_usage
            
            visited.remove(current_func)
            return max_path, max_usage
        
        max_path, _ = find_max_branch(start_func)
        return max_path

    def get_memory_sections(self):
        """Iegūst .data un .bss sekciju izmērus no ELF faila"""
        result = subprocess.run(
            ["avr-size", self.elf_file],
            capture_output=True, text=True
        )
        # Parsē izvadi: "text    data     bss"
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            sizes = lines[1].split()
            return {
                'data': int(sizes[1]),
                'bss': int(sizes[2])
            }
        return {'data': 0, 'bss': 0}
    
    def generate_report(self, static_analysis):
        """Ģenerē visaptverošu pārskatu par steka izmantojuma analīzi."""
        sections = self.get_memory_sections()
        data_size = sections.get('data', 0) + sections.get('bss', 0)
        available_stack = self.ram_size - data_size
        
        # Teksta atskaite
        report = [
            f"Stack Analysis Report for {os.path.basename(self.source_file)}",
            "=" * 60,
            f"MCU Type: {self.mcu_type}",
            f"RAM Size: {self.ram_size} bytes",
            f"Data Size (.data + .bss): {data_size} bytes",
            f"Available Stack Space: {available_stack} bytes",
            "",
            "Static Analysis Results:",
            "-" * 30,
            f"Maximum Stack Usage (with 10% safety margin): {static_analysis['max_stack_usage']} bytes",
            f"Calculated Stack Usage: {static_analysis['raw_max_usage']} bytes",
            f"Free Stack Space: {int(available_stack - static_analysis['max_stack_usage'])} bytes",
            f"Stack Usage Percentage: {(static_analysis['max_stack_usage'] / self.ram_size * 100):.1f}%",
            "",
            "Function Stack Usage (includes 2 bytes return addr):",
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
            report.append("Recursive Functions (detected from assembly):")
            report.append("-" * 30)
            for func in static_analysis['recursive_functions']:
                limit = static_analysis['recursion_limits'].get(func, "unknown")
                reduce_info = static_analysis['reduction_info'].get(func, {})

                # Formatē rekursijas veidu ar faktoru
                recursion_type = reduce_info.get('type', 'unknown')
                factor = reduce_info.get('value', 1)
                
                if recursion_type == 'subtraction':
                    type_str = f"subtraction by {factor}"
                elif recursion_type == 'division':
                    type_str = f"division by {factor}"
                else:
                    type_str = recursion_type
                
                report.append(f"{func} (recursion limit: {limit}, type: {type_str})")
        
        # Pievieno izsaukuma grafa informāciju
        if static_analysis['call_graph']:
            report.append("")
            report.append("Function Call Graph:")
            report.append("-" * 30)
            for func, calls in static_analysis['call_graph'].items():
                if calls:
                    calls_str = ", ".join(calls)
                    report.append(f"{func} -> {calls_str}")
                else:
                    report.append(f"{func} -> (leaf function)")
        
        # Pievieno visu ceļu informāciju
        if static_analysis.get('all_paths'):
            report.append("")
            report.append("All Stack Paths:")
            report.append("-" * 30)
            for i, path_info in enumerate(static_analysis['all_paths']):
                report.append(f"{i+1}. {path_info['details']}")

        return "\n".join(report)

# Galvenā analīzes funkcija
def analyze_stack(source_file, mcu_type="atmega328p", ram_size=2048, optimization="O0", extra_flags=None):
    """Analizē steka izmantojumu AVR C sākuma failam."""
    try:
        # Inicializē analizatoru
        analyzer = AVRCStackAnalyzer(
            source_file, 
            mcu_type=mcu_type, 
            ram_size=ram_size, 
            optimization=optimization,
            compiler_flags=extra_flags
        )
        
        # Kompilē kodu
        analyzer.compile_c_code()
        
        # Iegūst steka lietošanas pārskatu no GCC
        gcc_stack_usage = analyzer.collect_stack_usage_reports()
        
        # Disamblē kodu
        asm_code = analyzer.disassemble_avr()
        
        # Analizē statiskās steka lietojumu
        static_analysis = analyzer.analyze_static_stack_usage(asm_code, gcc_stack_usage)
        
        # Ģenerē atskaiti
        report = analyzer.generate_report(static_analysis)
        
        # Izdrukā pagaidu direktorijas ceļu atkļūdošanas nolūkos
        logger.info(f"Temporary directory: {analyzer.temp_dir}")
        
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
    parser.add_argument("-r", "--ram", type=int, default=2048, help="RAM size in bytes (default: 2048)")
    parser.add_argument("-o", "--optimization", default="O0", help="Optimization level: O0 (none), O1 (basic), O2 (standard), O3 (aggressive), Os (size), Og (debug) (default: O0)")
    parser.add_argument("-l", "--log-level", default="warning", help="Logging level: debug, info, warning, error, critical (default: warning)")
    parser.add_argument("-c", "--compiler-flags", help="Additional GCC compiler flags")
    
    args = parser.parse_args()
    
    # Uzstāda žurnālošanu ar norādīto līmeni
    setup_logging(args.log_level)

    # Normalizē MCU tipu (case-insensitive)
    mcu_type = args.mcu.lower()

    # Parsē kompilatoru karogus
    extra_flags = args.compiler_flags.split() if args.compiler_flags else None
    
    # Veic analīzi
    result = analyze_stack(
        args.source_file,
        mcu_type=mcu_type,
        ram_size=args.ram,
        optimization=args.optimization,
        extra_flags=extra_flags
    )
    
    # Izdrukā rezultātus
    print(result)

if __name__ == "__main__":
    main()