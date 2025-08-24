#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASAP7 Liberty Parser for Lib2Vec Framework
This module implements the liberty file parsing functionality for the ASAP7 cell library
as described in the Lib2Vec paper.
"""

import os
import sys
import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import logging

# Install liberty-parser if not available
try:
    from liberty.parser import parse_liberty
except ImportError:
    print("Installing liberty-parser...")
    os.system("pip install liberty-parser")
    from liberty.parser import parse_liberty

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ASAP7Parser:
    """
    Parser for ASAP7 Liberty files to extract cell properties for Lib2Vec
    """
    
    def __init__(self, liberty_file_path: str):
        """
        Initialize the parser with a liberty file path
        
        Args:
            liberty_file_path (str): Path to the ASAP7 liberty file
        """
        self.liberty_file_path = liberty_file_path
        self.library = None
        self.cells = {}
        self.cell_types = {}
        self.pin_mappings = {}
        
        # Properties to extract (as mentioned in the paper)
        self.properties_to_extract = {
            'functional': ['function'],
            'electrical': ['cell_rise', 'cell_fall', 'rise_transition', 'fall_transition', 
                          'rise_power', 'fall_power']
        }
        
    def parse_liberty_file(self) -> bool:
      """
      Parse the liberty file and extract library information
      
      Returns:
          bool: True if parsing successful, False otherwise
      """
      try:
          logger.info(f"Parsing liberty file: {self.liberty_file_path}")
          
          # ³¢ÊÔ²»Í¬µÄ±àÂë
          encodings = ['utf-8', 'latin-1', 'iso-8859-1']
          content = None
          
          for encoding in encodings:
              try:
                  with open(self.liberty_file_path, 'r', encoding=encoding) as f:
                      content = f.read()
                  logger.info(f"Successfully read file with encoding: {encoding}")
                  break
              except UnicodeDecodeError as e:
                  logger.warning(f"Failed to read with encoding {encoding}: {e}")
                  continue
          
          if content is None:
              logger.error("Failed to read file with any encoding")
              return False
          
          # ³¢ÊÔÔ¤´¦ÀíÄÚÈÝÒÔÐÞ¸´³£¼ûÎÊÌâ
          content = self.preprocess_liberty_content(content)
          
          self.library = parse_liberty(content)
          
          logger.info("Successfully parsed liberty file")
          return True
          
      except Exception as e:
          logger.error(f"Error parsing liberty file: {e}")
          
          # Ìá¹©¸üÏêÏ¸µÄ´íÎóÐÅÏ¢
          if hasattr(e, 'lineno') and hasattr(e, 'offset'):
              logger.error(f"Error at line {e.lineno}, position {e.offset}")
              
              # ¶ÁÈ¡²¢ÏÔÊ¾´íÎóÐÐ
              try:
                  with open(self.liberty_file_path, 'r') as f:
                      lines = f.readlines()
                      if e.lineno <= len(lines):
                          error_line = lines[e.lineno - 1]
                          logger.error(f"Problematic line: {error_line.strip()}")
                          # ÏÔÊ¾´íÎóÎ»ÖÃ
                          marker = ' ' * (e.offset - 1) + '^'
                          logger.error(f"Position: {marker}")
              except:
                  pass
          
          return False

    def preprocess_liberty_content(self, content: str) -> str:
        # ÐÞ¸´³£¼ûµÄÓï·¨ÎÊÌâ
        lines = content.split('\n')
        processed_lines = []
        
        for i, line in enumerate(lines, 1):
            # Ìø¹ý¿ÕÐÐºÍ×¢ÊÍÐÐ
            if not line.strip() or line.strip().startswith('//') or line.strip().startswith('/*'):
                processed_lines.append(line)
                continue
                
            # ÐÞ¸´¿ÉÄÜµÄÎÊÌâ
            # ÀýÈç£ºÈ·±£ÊôÐÔÖµÓÃÒýºÅÀ¨ÆðÀ´
            if ':' in line and not ('"' in line or "'" in line):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key, value = parts
                    value = value.strip()
                    if value and not (value.startswith('"') and value.endswith('"')):
                        line = f'{key}:"{value}"'
            
            processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def extract_cell_information(self) -> Dict[str, Any]:
        """
        Extract detailed cell information from the parsed liberty file
        
        Returns:
            Dict containing cell information organized by cell name
        """
        if not self.library:
            logger.error("Library not parsed yet. Call parse_liberty_file() first.")
            return {}
        
        cells_info = {}
        
        for cell in self.library.get_groups('cell'):
            cell_name = cell.args[0]
            cell_info = self._extract_single_cell_info(cell)
            cells_info[cell_name] = cell_info
            
            # Group cells by functional type (as mentioned in paper - 190 cells -> 86 types)
            func_expr = cell_info.get('function', '')
            if func_expr:
                cell_type = self._determine_cell_type(cell_name, func_expr)
                if cell_type not in self.cell_types:
                    self.cell_types[cell_type] = []
                self.cell_types[cell_type].append(cell_name)
        
        self.cells = cells_info
        logger.info(f"Extracted information for {len(cells_info)} cells")
        logger.info(f"Identified {len(self.cell_types)} cell types")
        
        return cells_info
    
    def _extract_single_cell_info(self, cell) -> Dict[str, Any]:
        """
        Extract information from a single cell
        
        Args:
            cell: Liberty cell object
            
        Returns:
            Dict containing cell information
        """
        cell_info = {
            'name': cell.args[0],
            'pins': {},
            'timing_arcs': [],
            'function': '',
            'area': 0.0,
            'leakage_power': 0.0
        }
        
        # Extract basic cell attributes
        if hasattr(cell, 'area'):
            cell_info['area'] = float(cell.area)
        
        if hasattr(cell, 'cell_leakage_power'):
            cell_info['leakage_power'] = float(cell.cell_leakage_power)
        
        # Extract pin information
        for pin in cell.get_groups('pin'):
            pin_name = pin.args[0]
            pin_info = self._extract_pin_info(pin)
            cell_info['pins'][pin_name] = pin_info
            
            # Extract function if it's an output pin
            if pin_info.get('direction') == 'output' and hasattr(pin, 'function'):
                cell_info['function'] = str(pin.function)
        
        # Extract timing information
        cell_info['timing_arcs'] = self._extract_timing_arcs(cell)
        
        return cell_info
    
    def _extract_pin_info(self, pin) -> Dict[str, Any]:
        """
        Extract information from a single pin
        
        Args:
            pin: Liberty pin object
            
        Returns:
            Dict containing pin information
        """
        pin_info = {
            'name': pin.args[0],
            'direction': '',
            'capacitance': 0.0,
            'max_capacitance': 0.0,
            'function': ''
        }
        
        # Extract pin attributes
        if hasattr(pin, 'direction'):
            pin_info['direction'] = str(pin.direction)
            
        if hasattr(pin, 'capacitance'):
            pin_info['capacitance'] = float(pin.capacitance)
            
        if hasattr(pin, 'max_capacitance'):
            pin_info['max_capacitance'] = float(pin.max_capacitance)
            
        if hasattr(pin, 'function'):
            pin_info['function'] = str(pin.function)
        
        return pin_info
    
    def _extract_timing_arcs(self, cell) -> List[Dict[str, Any]]:
        """
        Extract timing arc information from a cell
        
        Args:
            cell: Liberty cell object
            
        Returns:
            List of timing arc dictionaries
        """
        timing_arcs = []
        
        for pin in cell.get_groups('pin'):
            pin_name = pin.args[0]
            
            for timing in pin.get_groups('timing'):
                arc_info = {
                    'output_pin': pin_name,
                    'related_pin': '',
                    'timing_sense': '',
                    'timing_type': '',
                    'cell_rise': None,
                    'cell_fall': None,
                    'rise_transition': None,
                    'fall_transition': None,
                    'rise_power': None,
                    'fall_power': None
                }
                
                # Extract timing attributes
                if hasattr(timing, 'related_pin'):
                    arc_info['related_pin'] = str(timing.related_pin).strip('"')
                    
                if hasattr(timing, 'timing_sense'):
                    arc_info['timing_sense'] = str(timing.timing_sense)
                    
                if hasattr(timing, 'timing_type'):
                    arc_info['timing_type'] = str(timing.timing_type)
                
                # Extract lookup tables for delays and transitions
                arc_info.update(self._extract_timing_tables(timing))
                
                timing_arcs.append(arc_info)
        
        return timing_arcs
    
    def _extract_timing_tables(self, timing) -> Dict[str, Any]:
        """
        Extract timing lookup tables (as mentioned in paper - lookup tables for delay/power)
        
        Args:
            timing: Liberty timing object
            
        Returns:
            Dict containing timing table information
        """
        tables = {}
        
        # Define the timing table types to extract
        table_types = ['cell_rise', 'cell_fall', 'rise_transition', 'fall_transition',
                      'rise_power', 'fall_power']
        
        for table_type in table_types:
            if hasattr(timing, table_type):
                table = getattr(timing, table_type)
                table_info = self._parse_lookup_table(table)
                tables[table_type] = table_info
        
        return tables
    
    def _parse_lookup_table(self, table) -> Dict[str, Any]:
        """
        Parse a lookup table from liberty format
        
        Args:
            table: Liberty table object
            
        Returns:
            Dict containing parsed table information
        """
        table_info = {
            'index_1': [],  # input slew values
            'index_2': [],  # output load values  
            'values': []    # delay/transition/power values
        }
        
        try:
            if hasattr(table, 'index_1'):
                # Parse index_1 (input slew)
                index_1_str = str(table.index_1).strip('"')
                table_info['index_1'] = [float(x.strip()) for x in index_1_str.split(',')]
            
            if hasattr(table, 'index_2'):
                # Parse index_2 (output load)
                index_2_str = str(table.index_2).strip('"')
                table_info['index_2'] = [float(x.strip()) for x in index_2_str.split(',')]
            
            if hasattr(table, 'values'):
                # Parse values matrix
                values_str = str(table.values).strip('"')
                # Remove any leading/trailing whitespace and split by lines
                lines = [line.strip() for line in values_str.split('\\') if line.strip()]
                values_matrix = []
                for line in lines:
                    if line:
                        row = [float(x.strip()) for x in line.replace(',', ' ').split() if x.strip()]
                        if row:
                            values_matrix.append(row)
                table_info['values'] = values_matrix
                
        except Exception as e:
            logger.warning(f"Error parsing lookup table: {e}")
        
        return table_info
    
    def _determine_cell_type(self, cell_name: str, function: str) -> str:
        """
        Determine the cell type based on cell name and function
        This groups cells with same functionality but different drive strengths
        
        Args:
            cell_name (str): Name of the cell
            function (str): Functional expression
            
        Returns:
            str: Cell type identifier
        """
        # Remove drive strength indicators and library-specific suffixes
        # ASAP7 naming convention: [function][drive_strength]x[threshold]_ASAP7_75t_[variant]
        
        # Extract base function name
        base_name = cell_name.split('x')[0]  # Remove drive strength part
        
        # Common ASAP7 cell type mappings
        if 'INV' in base_name:
            return 'INV'
        elif 'BUF' in base_name:
            return 'BUF'
        elif 'NAND' in base_name:
            if '2' in base_name:
                return 'NAND2'
            elif '3' in base_name:
                return 'NAND3'
            elif '4' in base_name:
                return 'NAND4'
            else:
                return 'NAND'
        elif 'NOR' in base_name:
            if '2' in base_name:
                return 'NOR2'
            elif '3' in base_name:
                return 'NOR3'
            elif '4' in base_name:
                return 'NOR4'
            else:
                return 'NOR'
        elif 'AND' in base_name:
            if '2' in base_name:
                return 'AND2'
            elif '3' in base_name:
                return 'AND3'
            elif '4' in base_name:
                return 'AND4'
            else:
                return 'AND'
        elif 'OR' in base_name:
            if '2' in base_name:
                return 'OR2'
            elif '3' in base_name:
                return 'OR3'
            elif '4' in base_name:
                return 'OR4'
            else:
                return 'OR'
        elif 'XOR' in base_name:
            return 'XOR2' if '2' in base_name else 'XOR'
        elif 'XNOR' in base_name:
            return 'XNOR2' if '2' in base_name else 'XNOR'
        else:
            # For complex cells, use the base name
            return base_name
    
    def generate_input_conditions(self, num_slew_points: int = 150, 
                                num_load_points: int = 150) -> List[Tuple[float, float]]:
        """
        Generate input conditions for electrical similarity tests
        As mentioned in paper: 150x150 = 22,500 combinations
        
        Args:
            num_slew_points (int): Number of slew points to sample
            num_load_points (int): Number of load points to sample
            
        Returns:
            List of (slew, load) tuples
        """
        # Find the ranges across all cells
        min_slew, max_slew = float('inf'), 0
        min_load, max_load = float('inf'), 0
        
        for cell_info in self.cells.values():
            for arc in cell_info['timing_arcs']:
                for table_type in ['cell_rise', 'cell_fall', 'rise_transition', 'fall_transition']:
                    if arc.get(table_type):
                        table = arc[table_type]
                        if table.get('index_1'):
                            min_slew = min(min_slew, min(table['index_1']))
                            max_slew = max(max_slew, max(table['index_1']))
                        if table.get('index_2'):
                            min_load = min(min_load, min(table['index_2']))
                            max_load = max(max_load, max(table['index_2']))
        
        # Apply logarithmic transformation and uniform sampling
        log_min_slew, log_max_slew = np.log(min_slew), np.log(max_slew)
        log_min_load, log_max_load = np.log(min_load), np.log(max_load)
        
        log_slew_points = np.linspace(log_min_slew, log_max_slew, num_slew_points)
        log_load_points = np.linspace(log_min_load, log_max_load, num_load_points)
        
        slew_points = np.exp(log_slew_points)
        load_points = np.exp(log_load_points)
        
        # Generate all combinations
        conditions = []
        for slew in slew_points:
            for load in load_points:
                conditions.append((slew, load))
        
        logger.info(f"Generated {len(conditions)} input conditions")
        return conditions
    
    def interpolate_timing_value(self, table: Dict[str, Any], slew: float, load: float) -> float:
        """
        Interpolate timing value from lookup table for given slew and load
        
        Args:
            table (Dict): Timing lookup table
            slew (float): Input slew value
            load (float): Output load value
            
        Returns:
            float: Interpolated timing value
        """
        if not table or not table.get('values'):
            return 0.0
        
        index_1 = table.get('index_1', [])
        index_2 = table.get('index_2', [])
        values = table.get('values', [])
        
        if not index_1 or not index_2 or not values:
            return 0.0
        
        # Simple bilinear interpolation
        try:
            # Find bounding indices for slew
            i1 = 0
            while i1 < len(index_1) - 1 and index_1[i1 + 1] < slew:
                i1 += 1
            i2 = min(i1 + 1, len(index_1) - 1)
            
            # Find bounding indices for load  
            j1 = 0
            while j1 < len(index_2) - 1 and index_2[j1 + 1] < load:
                j1 += 1
            j2 = min(j1 + 1, len(index_2) - 1)
            
            # Perform bilinear interpolation
            if i1 == i2 and j1 == j2:
                return values[i1][j1]
            elif i1 == i2:
                t = (load - index_2[j1]) / (index_2[j2] - index_2[j1])
                return values[i1][j1] * (1 - t) + values[i1][j2] * t
            elif j1 == j2:
                t = (slew - index_1[i1]) / (index_1[i2] - index_1[i1])
                return values[i1][j1] * (1 - t) + values[i2][j1] * t
            else:
                # Full bilinear interpolation
                dx = index_1[i2] - index_1[i1]
                dy = index_2[j2] - index_2[j1]
                
                v11, v12 = values[i1][j1], values[i1][j2]
                v21, v22 = values[i2][j1], values[i2][j2]
                
                t1 = (slew - index_1[i1]) / dx
                t2 = (load - index_2[j1]) / dy
                
                return (v11 * (1 - t1) * (1 - t2) + 
                       v21 * t1 * (1 - t2) + 
                       v12 * (1 - t1) * t2 + 
                       v22 * t1 * t2)
                       
        except Exception as e:
            logger.warning(f"Error in interpolation: {e}")
            return 0.0
    
    def save_parsed_data(self, output_dir: str):
        """
        Save parsed data to JSON files for later use
        
        Args:
            output_dir (str): Directory to save the parsed data
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Save cell information
        with open(os.path.join(output_dir, 'cells.json'), 'w') as f:
            json.dump(self.cells, f, indent=2, default=str)
        
        # Save cell types grouping
        with open(os.path.join(output_dir, 'cell_types.json'), 'w') as f:
            json.dump(self.cell_types, f, indent=2)
        
        # Save summary statistics
        stats = {
            'total_cells': len(self.cells),
            'total_cell_types': len(self.cell_types),
            'cells_per_type': {k: len(v) for k, v in self.cell_types.items()}
        }
        
        with open(os.path.join(output_dir, 'parsing_stats.json'), 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Saved parsed data to {output_dir}")
        logger.info(f"Statistics: {stats['total_cells']} cells, {stats['total_cell_types']} types")
        
    def check_liberty_file(self) -> bool:
        try:
            with open(self.liberty_file_path, 'r') as f:
                lines = f.readlines()
            
            # ¼ì²éÎÄ¼þÊÇ·ñ°üº¬±ØÒªµÄ²¿·Ö
            has_cell = any('cell (' in line for line in lines)
            has_library = any('library (' in line for line in lines)
            
            if not (has_cell and has_library):
                logger.error("File doesn't appear to be a valid Liberty file")
                return False
                
            logger.info("File appears to be a valid Liberty file")
            return True
            
        except Exception as e:
            logger.error(f"Error checking file: {e}")
            return False

    def main():
        """
        Example usage of the ASAP7Parser
        """
        # Example liberty file path (modify according to your setup)
        liberty_file = "../data/asap7sc7p5t_27/LIB/NLDM/asap7sc7p5t_AO_LVT_TT_nldm_201020.lib"
        
        if not os.path.exists(liberty_file):
            print(f"Liberty file not found: {liberty_file}")
            print("Please provide the correct path to your ASAP7 liberty file")
            return
        
        # Create parser instance
        parser = ASAP7Parser(liberty_file)
        
        # ÏÈ¼ì²éÎÄ¼þ
        if not parser.check_liberty_file():
            print("Invalid Liberty file")
            exit(1)
        
        # Parse the liberty file
        if parser.parse_liberty_file():
            # Extract cell information
            cells = parser.extract_cell_information()
            
            # Generate input conditions for electrical tests
            conditions = parser.generate_input_conditions()
            
            # Save parsed data
            parser.save_parsed_data("asap7_parsed_data")
            
            print(f"Successfully parsed {len(cells)} cells")
            print(f"Identified {len(parser.cell_types)} cell types")
            print(f"Generated {len(conditions)} input conditions")
        else:
            print("Failed to parse liberty file")
    
    if __name__ == "__main__":
        main()
