"""
Veic AVR steka analizatora analīzi visiem C failiem un izvada kompaktu pārskatu
"""

import subprocess
import os
import glob
import re
import sys
from pathlib import Path

class BatchStackAnalyzer:
    def __init__(self, analyzer_script="avr-stack-analyzer-static.py"):
        self.analyzer_script = analyzer_script
        self.results = []
        
        # Pārbauda vai analizatora skripts eksistē
        if not os.path.exists(analyzer_script):
            print(f"Error: Analyzer script '{analyzer_script}' not found!")
            sys.exit(1)
    
    def find_c_files(self, directory="."):
        """Atrod visus C failus norādītajā direktorijā"""
        c_files = []
        
        # Meklē C failus
        for pattern in ["*.c"]:
            c_files.extend(glob.glob(os.path.join(directory, pattern)))
        
        # Izlaiž analizatora skriptu, ja tas būtu ar .c paplašinājumu
        c_files = [f for f in c_files if not f.endswith('.py')]
        
        return sorted(c_files)
    
    def run_analyzer(self, c_file, mcu="atmega328p", ram_size=2048, optimization="O0"):
        """Palaiž analizatoru vienam C failam"""
        cmd = [
            "python3", self.analyzer_script,
            c_file,
            "-m", mcu,
            "-r", str(ram_size),
            "-o", optimization,
            "-l", "warning"  # Tikai svarīgus paziņojumus
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 sekunžu timeout
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                error_msg = f"Analysis failed for {c_file}:\n{result.stderr}"
                print(f"Warning: {error_msg}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"Warning: Analysis timeout for {c_file}")
            return None
        except Exception as e:
            print(f"Warning: Error analyzing {c_file}: {e}")
            return None
    
    def parse_results(self, output, filename):
        """Parsē analizatora izvadi, lai iegūtu galvenās vērtības"""
        if not output:
            return None
        
        # Meklē maksimālo steka izmantojumu ar drošības rezervi
        max_pattern = r"Maximum Stack Usage \(with 10% safety margin\):\s*(\d+)\s*bytes"
        max_match = re.search(max_pattern, output)
        
        # Meklē aprēķināto steka izmantojumu
        calc_pattern = r"Calculated Stack Usage:\s*(\d+)\s*bytes"
        calc_match = re.search(calc_pattern, output)
        
        # Meklē datu izmēru (.data + .bss)
        data_pattern = r"Data Size \(\.data \+ \.bss\):\s*(\d+)\s*bytes"
        data_match = re.search(data_pattern, output)
        
        if max_match and calc_match and data_match:
            return {
                'filename': filename,
                'max_usage': int(max_match.group(1)),
                'calculated_usage': int(calc_match.group(1)),
                'data_size': int(data_match.group(1)),
                'success': True
            }
        else:
            # Mēģina atrast kļūdas ziņojumu
            error_pattern = r"Error:\s*(.+)"
            error_match = re.search(error_pattern, output)
            error_msg = error_match.group(1) if error_match else "Unknown parsing error"
            
            return {
                'filename': filename,
                'max_usage': 0,
                'calculated_usage': 0,
                'data_size': 0,
                'success': False,
                'error': error_msg
            }
    
    def analyze_all_files(self, directory=".", mcu="atmega328p", ram_size=2048, optimization="O0"):
        """Analizē visus C failus direktorijā"""
        c_files = self.find_c_files(directory)
        
        if not c_files:
            print("No C files found in the specified directory!")
            return
        
        print(f"Found {len(c_files)} C files to analyze...")
        print("=" * 100)
        
        for c_file in c_files:
            print(f"Analyzing {c_file}...", end=" ", flush=True)
            
            output = self.run_analyzer(c_file, mcu, ram_size, optimization)
            result = self.parse_results(output, os.path.basename(c_file))
            
            if result:
                self.results.append(result)
                if result['success']:
                    print("✓ Done")
                else:
                    print(f"✗ Failed: {result.get('error', 'Unknown error')}")
            else:
                print("✗ Failed to run analyzer")
        
        print("=" * 100)
    
    def print_summary(self):
        """Izvada kompaktu rezultātu pārskatu"""
        if not self.results:
            print("No results to display!")
            return
        
        print("\nAVR STACK ANALYSIS RESULTS")
        print("=" * 100)
        
        # Kārto rezultātus pēc maksimālā steka izmantojuma
        successful_results = [r for r in self.results if r['success']]
        failed_results = [r for r in self.results if not r['success']]
        
        successful_results.sort(key=lambda x: x['max_usage'], reverse=True)
        
        # Izvada veiksmīgos rezultātus
        if successful_results:
            print(f"{'Program':<25} {'Max Usage (10%)':<18} {'Calculated Usage':<18} {'Data Size':<15}")
            print("-" * 95)
            
            for result in successful_results:
                print(f"{result['filename']:<25} "
                      f"{result['max_usage']:>12} bytes    "
                      f"{result['calculated_usage']:>12} bytes    "
                      f"{result['data_size']:>9} bytes")
        
        # Izvada neveiksmīgos rezultātus
        if failed_results:
            print(f"\nFAILED ANALYSES ({len(failed_results)} files):")
            print("-" * 50)
            for result in failed_results:
                error_msg = result.get('error', 'Unknown error')
                print(f"{result['filename']:<25} Error: {error_msg}")
        
        # Statistika
        if successful_results:
            print(f"\nSTATISTICS:")
            print("-" * 20)
            print(f"Successfully analyzed: {len(successful_results)}/{len(self.results)} files")

def main():
    """Galvenā funkcija"""
    print("AVR Stack Analysis Batch Runner")
    print("=" * 40)
    
    # Konfigurācijas parametri
    MCU_TYPE = "atmega328p"
    RAM_SIZE = 2048
    OPTIMIZATION = "O0"
    
    # Inicializē analizatoru
    analyzer = BatchStackAnalyzer("avr-stack-analyzer-static.py")
    
    # Analizē visus failus
    analyzer.analyze_all_files(
        directory=".",  # Pašreizējā direktorija
        mcu=MCU_TYPE,
        ram_size=RAM_SIZE,
        optimization=OPTIMIZATION
    )
    
    # Izvada rezultātus
    analyzer.print_summary()

if __name__ == "__main__":
    main()