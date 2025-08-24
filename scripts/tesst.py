# Complete Optimized Liberty Parser for Lib2Vec
# High-performance version with progress tracking and error handling

import re
import json
from collections import defaultdict
import time
import signal
import sys
import os

class CompleteLib2VecLibertyParser:
    """
    Complete optimized Liberty parser for Lib2Vec framework
    Designed for high performance with large Liberty files
    """
    
    def __init__(self, debug_mode=True, timeout_minutes=60):
        self.library_info = {}
        self.cells = {}
        self.debug_mode = debug_mode
        self.timeout_minutes = timeout_minutes
        self.processed_cells = 0
        
        # Set up timeout handler
        if timeout_minutes > 0:
            signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(timeout_minutes * 60)
    
    def _timeout_handler(self, signum, frame):
        """Handle timeout signal"""
        print(f"ERROR: Parsing timeout after {self.timeout_minutes} minutes")
        print(f"Processed {self.processed_cells} cells before timeout")
        sys.exit(1)
    
    def parse_liberty_file(self, filename):
        """Main parsing method with comprehensive error handling"""
        
        if not os.path.exists(filename):
            print(f"ERROR: File not found: {filename}")
            return None
        
        print(f"Starting to parse file: {filename}")
        start_time = time.time()
        
        # Read file with error handling
        print("Reading file...")
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"ERROR reading file: {e}")
            return None
            
        file_size_mb = len(content) / 1024 / 1024
        print(f"File size: {file_size_mb:.2f} MB ({len(content)} characters)")
        
        if file_size_mb > 100:
            print("WARNING: Large file detected. This may take a while...")
        
        # Preprocessing
        print("Removing comments...")
        content = self._remove_comments_optimized(content)
        
        # Extract library information
        print("Extracting library information...")
        self._extract_library_info(content)
        print(f"Library: {self.library_info.get('name', 'Unknown')}")
        
        # Extract cell information
        print("Extracting cell information...")
        self._extract_cells_complete(content)
        
        # Format data
        print("Formatting data for Lib2Vec...")
        result = self._format_for_lib2vec()
        
        end_time = time.time()
        total_time = end_time - start_time
        print(f"Parsing completed successfully!")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Average time per cell: {total_time/max(1, len(self.cells)):.3f} seconds")
        
        # Clear timeout
        if self.timeout_minutes > 0:
            signal.alarm(0)
        
        return result
    
    def _remove_comments_optimized(self, content):
        """Optimized comment removal with progress tracking"""
        
        if not isinstance(content, str):
            content = str(content)
        
        original_size = len(content)
        
        # Remove line comments first (faster)
        lines = content.split('\n')
        cleaned_lines = []
        
        for i, line in enumerate(lines):
            if self.debug_mode and i % 10000 == 0 and i > 0:
                print(f"  Processing line {i}/{len(lines)}")
            
            # Simple line comment removal
            comment_pos = line.find('//')
            if comment_pos >= 0:
                line = line[:comment_pos]
            cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        # Remove block comments
        print("  Removing block comments...")
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        removed_size = original_size - len(content)
        print(f"  Removed {removed_size} characters ({removed_size/original_size*100:.1f}%)")
        
        return content
    
    def _extract_library_info(self, content):
        """Extract comprehensive library information"""
        
        # Extract library name
        lib_match = re.search(r'library\s*\(\s*([^)]+)\s*\)', content)
        if lib_match:
            self.library_info['name'] = lib_match.group(1).strip().strip('"')
        
        # Extract basic parameters
        basic_params = [
            'delay_model', 'nom_voltage', 'nom_temperature', 'nom_process',
            'default_max_transition', 'default_fanout_load', 'default_inout_pin_cap',
            'default_input_pin_cap', 'default_output_pin_cap', 'in_place_swap_mode'
        ]
        
        for param in basic_params:
            pattern = fr'{param}\s*:\s*([^;]+);'
            match = re.search(pattern, content)
            if match:
                value = match.group(1).strip().strip('"')
                try:
                    # Try to convert to float
                    self.library_info[param] = float(value)
                except:
                    # Keep as string if conversion fails
                    self.library_info[param] = value
        
        # Extract voltage mapping
        voltage_maps = re.findall(r'voltage_map\s*\(\s*([^,]+),\s*([^)]+)\)', content)
        if voltage_maps:
            self.library_info['voltage_maps'] = {}
            for vm in voltage_maps:
                name = vm[0].strip()
                try:
                    voltage = float(vm[1].strip().rstrip(';'))
                    self.library_info['voltage_maps'][name] = voltage
                except:
                    pass
        
        # Extract operating conditions
        op_cond_pattern = r'operating_conditions\s*\(\s*([^)]+)\s*\)\s*{([^}]+)}'
        op_cond_match = re.search(op_cond_pattern, content)
        if op_cond_match:
            self.library_info['operating_conditions'] = op_cond_match.group(1).strip()
        
        print(f"  Found {len(self.library_info)} library parameters")
    
    def _extract_cells_complete(self, content):
        """Complete cell extraction with robust parsing"""
        
        # Find all cell start positions
        cell_pattern = re.compile(r'cell\s*\(\s*([^)]+)\s*\)\s*{')
        cell_starts = []
        
        for match in cell_pattern.finditer(content):
            cell_name = match.group(1).strip().strip('"')
            cell_starts.append((match.start(), match.end(), cell_name))
        
        total_cells = len(cell_starts)
        print(f"Found {total_cells} cells to process")
        
        if total_cells == 0:
            print("WARNING: No cells found in the file")
            return
        
        # Process each cell
        for i, (start_pos, end_pos, cell_name) in enumerate(cell_starts):
            self.processed_cells = i + 1
            
            if self.debug_mode:
                if i % 50 == 0 or i == total_cells - 1:
                    progress = (i + 1) / total_cells * 100
                    print(f"  Processing cell {i+1}/{total_cells} ({progress:.1f}%): {cell_name}")
            
            # Find matching closing brace
            cell_body = self._extract_cell_body(content, end_pos)
            
            if cell_body is not None:
                try:
                    cell_info = self._parse_single_cell_complete(cell_name, cell_body)
                    self.cells[cell_name] = cell_info
                except Exception as e:
                    if self.debug_mode:
                        print(f"    WARNING: Failed to parse cell {cell_name}: {e}")
            else:
                if self.debug_mode:
                    print(f"    WARNING: Could not extract body for cell {cell_name}")
        
        print(f"Successfully parsed {len(self.cells)}/{total_cells} cells")
    
    def _extract_cell_body(self, content, start_pos):
        """Extract cell body by matching braces"""
        
        brace_count = 1
        pos = start_pos
        max_search = len(content)
        
        while pos < max_search and brace_count > 0:
            char = content[pos]
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            pos += 1
        
        if brace_count == 0:
            return content[start_pos:pos-1]
        else:
            return None
    
    def _parse_single_cell_complete(self, cell_name, cell_body):
        """Complete single cell parsing with all attributes"""
        
        cell_info = {
            'name': cell_name,
            'area': 0.0,
            'pins': {},
            'function': None,
            'timing_arcs': [],
            'power_info': {},
            'attributes': {},
            'leakage_power': 0.0,
            'cell_footprint': None
        }
        
        # Extract area
        area_match = re.search(r'area\s*:\s*([^;]+);', cell_body)
        if area_match:
            try:
                cell_info['area'] = float(area_match.group(1))
            except:
                cell_info['area'] = 0.0
        
        # Extract leakage power
        leakage_match = re.search(r'cell_leakage_power\s*:\s*([^;]+);', cell_body)
        if leakage_match:
            try:
                cell_info['leakage_power'] = float(leakage_match.group(1))
            except:
                cell_info['leakage_power'] = 0.0
        
        # Extract cell footprint
        footprint_match = re.search(r'cell_footprint\s*:\s*([^;]+);', cell_body)
        if footprint_match:
            cell_info['cell_footprint'] = footprint_match.group(1).strip().strip('"')
        
        # Extract pins
        self._extract_pins_complete(cell_body, cell_info)
        
        # Extract function
        function_match = re.search(r'function\s*:\s*"([^"]+)"', cell_body)
        if function_match:
            cell_info['function'] = function_match.group(1)
        
        return cell_info
    
    def _extract_pins_complete(self, cell_body, cell_info):
        """Complete pin extraction with timing and power info"""
        
        pin_pattern = re.compile(r'pin\s*\(\s*([^)]+)\s*\)\s*{')
        pin_matches = list(pin_pattern.finditer(cell_body))
        
        for match in pin_matches:
            pin_name = match.group(1).strip().strip('"')
            
            # Extract pin body
            pin_body = self._extract_cell_body(cell_body, match.end())
            
            if pin_body:
                pin_info = self._parse_pin_complete(pin_name, pin_body)
                cell_info['pins'][pin_name] = pin_info
    
    def _parse_pin_complete(self, pin_name, pin_body):
        """Complete pin parsing with all attributes"""
        
        pin_info = {
            'name': pin_name,
            'direction': None,
            'function': None,
            'capacitance': 0.0,
            'max_transition': None,
            'timing': [],
            'power': [],
            'max_capacitance': None,
            'min_capacitance': None
        }
        
        # Basic pin attributes
        attributes = {
            'direction': str,
            'function': str,
            'capacitance': float,
            'max_transition': float,
            'max_capacitance': float,
            'min_capacitance': float
        }
        
        for attr, attr_type in attributes.items():
            pattern = fr'{attr}\s*:\s*([^;]+);'
            match = re.search(pattern, pin_body)
            if match:
                value = match.group(1).strip().strip('"')
                try:
                    if attr_type == float:
                        pin_info[attr] = float(value)
                    else:
                        pin_info[attr] = value
                except:
                    if attr_type == float:
                        pin_info[attr] = 0.0
                    else:
                        pin_info[attr] = value
        
        # Count timing arcs (simplified)
        timing_count = len(re.findall(r'timing\s*\(\s*\)', pin_body))
        pin_info['timing_arc_count'] = timing_count
        
        # Count power arcs (simplified)
        power_count = len(re.findall(r'internal_power\s*\(\s*\)', pin_body))
        pin_info['power_arc_count'] = power_count
        
        return pin_info
    
    def _format_for_lib2vec(self):
        """Format data for Lib2Vec with comprehensive statistics"""
        
        lib2vec_data = {
            'library_info': self.library_info,
            'cells': [],
            'statistics': {
                'total_cells': len(self.cells),
                'pin_count_distribution': defaultdict(int),
                'function_types': defaultdict(int),
                'cell_types': defaultdict(int),
                'area_distribution': {
                    'min': float('inf'),
                    'max': 0.0,
                    'avg': 0.0,
                    'total': 0.0
                },
                'timing_arcs_total': 0,
                'power_arcs_total': 0
            }
        }
        
        total_area = 0.0
        min_area = float('inf')
        max_area = 0.0
        
        for cell_name, cell_info in self.cells.items():
            
            # Calculate statistics
            pin_count = len(cell_info['pins'])
            lib2vec_data['statistics']['pin_count_distribution'][pin_count] += 1
            
            if cell_info['function']:
                func_type = self._categorize_function(cell_info['function'])
                lib2vec_data['statistics']['function_types'][func_type] += 1
            
            cell_type = self._infer_cell_type(cell_name, cell_info)
            lib2vec_data['statistics']['cell_types'][cell_type] += 1
            
            # Area statistics
            area = cell_info['area']
            total_area += area
            min_area = min(min_area, area)
            max_area = max(max_area, area)
            
            # Count timing and power arcs
            timing_arcs = sum(pin['timing_arc_count'] for pin in cell_info['pins'].values())
            power_arcs = sum(pin['power_arc_count'] for pin in cell_info['pins'].values())
            
            lib2vec_data['statistics']['timing_arcs_total'] += timing_arcs
            lib2vec_data['statistics']['power_arcs_total'] += power_arcs
            
            # Format cell data
            formatted_pins = []
            for pin_name, pin_info in cell_info['pins'].items():
                formatted_pin = {
                    'name': pin_name,
                    'direction': pin_info['direction'],
                    'capacitance': pin_info['capacitance'],
                    'timing_arc_count': pin_info['timing_arc_count'],
                    'power_arc_count': pin_info['power_arc_count']
                }
                formatted_pins.append(formatted_pin)
            
            formatted_cell = {
                'name': cell_name,
                'area': area,
                'leakage_power': cell_info['leakage_power'],
                'pin_count': pin_count,
                'pins': formatted_pins,
                'function': cell_info['function'],
                'cell_type': cell_type,
                'cell_footprint': cell_info['cell_footprint'],
                'timing_arcs': timing_arcs,
                'power_arcs': power_arcs
            }
            
            lib2vec_data['cells'].append(formatted_cell)
        
        # Finalize area statistics
        if len(self.cells) > 0:
            lib2vec_data['statistics']['area_distribution'] = {
                'min': min_area if min_area != float('inf') else 0.0,
                'max': max_area,
                'avg': total_area / len(self.cells),
                'total': total_area
            }
        
        return lib2vec_data
    
    def _categorize_function(self, function):
        """Categorize cell function type"""
        if not function:
            return 'unknown'
        
        function = function.lower()
        
        if 'and' in function and 'nand' not in function:
            return 'and_gate'
        elif 'nand' in function:
            return 'nand_gate'
        elif 'or' in function and 'nor' not in function:
            return 'or_gate'
        elif 'nor' in function:
            return 'nor_gate'
        elif 'not' in function or function.startswith('!'):
            return 'inverter'
        elif 'xor' in function:
            return 'xor_gate'
        elif 'mux' in function:
            return 'multiplexer'
        elif 'latch' in function or 'dff' in function or 'ff' in function:
            return 'sequential'
        elif 'buf' in function:
            return 'buffer'
        else:
            return 'combinational'
    
    def _infer_cell_type(self, cell_name, cell_info):
        """Infer cell type from name and characteristics"""
        
        name_lower = cell_name.lower()
        
        # Pattern-based inference
        patterns = {
            'and': 'AND',
            'nand': 'NAND', 
            'or': 'OR',
            'nor': 'NOR',
            'inv': 'INV',
            'not': 'INV',
            'xor': 'XOR',
            'buf': 'BUF',
            'mux': 'MUX',
            'dff': 'DFF',
            'latch': 'LATCH',
            'adder': 'ADDER',
            'aoi': 'AOI',
            'oai': 'OAI'
        }
        
        for pattern, cell_type in patterns.items():
            if pattern in name_lower:
                return cell_type
        
        # Pin count based inference
        pin_count = len(cell_info['pins'])
        if pin_count <= 2:
            return 'BASIC'
        elif pin_count <= 4:
            return 'SIMPLE'
        elif pin_count <= 8:
            return 'MEDIUM'
        else:
            return 'COMPLEX'
    
    def save_lib2vec_format(self, data, output_file):
        """Save data in Lib2Vec JSON format with compression"""
        
        try:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, separators=(',', ': '))
            
            file_size = os.path.getsize(output_file) / 1024 / 1024
            print(f"Data saved to: {output_file} ({file_size:.2f} MB)")
            return True
        except Exception as e:
            print(f"ERROR saving file: {e}")
            return False
    
    def print_statistics(self, data):
        """Print comprehensive parsing statistics"""
        
        stats = data['statistics']
        lib_info = data['library_info']
        
        print("\n" + "="*50)
        print("LIBERTY PARSING STATISTICS")
        print("="*50)
        
        print(f"Library name: {lib_info.get('name', 'Unknown')}")
        print(f"Delay model: {lib_info.get('delay_model', 'Unknown')}")
        print(f"Nominal voltage: {lib_info.get('nom_voltage', 'Unknown')} V")
        print(f"Nominal temperature: {lib_info.get('nom_temperature', 'Unknown')}")
        
        print(f"\nTotal cells: {stats['total_cells']}")
        print(f"Total timing arcs: {stats['timing_arcs_total']}")
        print(f"Total power arcs: {stats['power_arcs_total']}")
        
        print(f"\nArea statistics:")
        area_stats = stats['area_distribution']
        print(f"  Total area: {area_stats['total']:.6f}")
        print(f"  Average area: {area_stats['avg']:.6f}")
        print(f"  Min area: {area_stats['min']:.6f}")
        print(f"  Max area: {area_stats['max']:.6f}")
        
        print(f"\nPin count distribution:")
        for pin_count, count in sorted(stats['pin_count_distribution'].items()):
            percentage = count / stats['total_cells'] * 100
            print(f"  {pin_count} pins: {count} cells ({percentage:.1f}%)")
        
        print(f"\nFunction type distribution:")
        for func_type, count in sorted(stats['function_types'].items()):
            percentage = count / sum(stats['function_types'].values()) * 100
            print(f"  {func_type}: {count} cells ({percentage:.1f}%)")
        
        print(f"\nCell type distribution:")
        for cell_type, count in sorted(stats['cell_types'].items()):
            percentage = count / stats['total_cells'] * 100
            print(f"  {cell_type}: {count} cells ({percentage:.1f}%)")

# Main execution function
def main():
    """Main function with comprehensive testing"""
    
    # Configuration
    input_file = "/home/mingya/lib2vec-reproduction/data/asap7/asap7sc7p5t_27/LIB/NLDM/asap7sc7p5t_AO_LVT_TT_nldm_201020.lib"
    output_file = "complete_lib2vec_data.json"
    
    print("COMPLETE LIBERTY PARSER FOR LIB2VEC")
    print("="*50)
    
    # Create parser instance
    parser = CompleteLib2VecLibertyParser(debug_mode=True, timeout_minutes=60)
    
    try:
        # Parse the Liberty file
        data = parser.parse_liberty_file(input_file)
        
        if data is None:
            print("ERROR: Parsing failed")
            return None
        
        # Save the results
        if parser.save_lib2vec_format(data, output_file):
            print("File saved successfully")
        
        # Print statistics
        parser.print_statistics(data)
        
        return data
        
    except KeyboardInterrupt:
        print("\nParsing interrupted by user")
        print(f"Processed {parser.processed_cells} cells before interruption")
        return None
    except Exception as e:
        print(f"ERROR during parsing: {e}")
        import traceback
        traceback.print_exc()
        return None

# Quick test function
def quick_test():
    """Quick test with limited cell count"""
    
    class QuickTestParser(CompleteLib2VecLibertyParser):
        def _extract_cells_complete(self, content):
            super()._extract_cells_complete(content)
            if len(self.cells) > 10:
                # Keep only first 10 cells for quick test
                cell_items = list(self.cells.items())[:10]
                self.cells = dict(cell_items)
                print(f"Quick test: Limited to 10 cells")
    
    parser = QuickTestParser(debug_mode=True, timeout_minutes=5)
    input_file = "/home/mingya/lib2vec-reproduction/data/asap7/asap7sc7p5t_27/LIB/NLDM/asap7sc7p5t_AO_LVT_TT_nldm_201020.lib"
    
    print("QUICK TEST MODE")
    print("="*30)
    
    data = parser.parse_liberty_file(input_file)
    if data:
        parser.print_statistics(data)
        return True
    return False

if __name__ == "__main__":
    # Run quick test first
    print("Running quick test...")
    if quick_test():
        print("\nQuick test successful!")
        print("\nStarting complete parsing...")
        main()
    else:
        print("Quick test failed. Please check the file path and format.")