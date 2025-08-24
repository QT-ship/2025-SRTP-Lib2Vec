#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 优化版本的Liberty解析器
import re
import json
from collections import defaultdict
import time

class OptimizedLib2VecLibertyParser:
    
    def __init__(self):
        self.library_info = {}
        self.cells = {}
        self.debug_mode = True  # 添加调试模式
        
    def parse_liberty_file(self, filename):
        
        
        print(f"begin parser: {filename}")
        start_time = time.time()
        
        # 读取文件
        print("reading file...")
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"error:couldn't find file {filename}")
            return None
        except Exception as e:
            print(f"error when reading files: {e}")
            return None
            
        print(f"file: {len(content)/1024/1024:.2f} MB")
        
        # 预处理
        print("removing interpretion...")
        content = self._remove_comments_optimized(content)
        
        # 提取库信息
        print("exacting lib data...")
        self._extract_library_info(content)
        
        # 提取单元信息 - 优化版本
        print("exacting cell data...")
        self._extract_cells_optimized(content)
        
        # 格式化
        print("formatting data...")
        result = self._format_for_lib2vec()
        
        end_time = time.time()
        print(f"successfully parser! time: {end_time - start_time:.2f} second")
        
        return result
    
    def _remove_comments_optimized(self, content):
        
        if not isinstance(content, str):
            content = str(content)
        
        # 使用更高效的正则表达式
        # 先移除行注释（更快）
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # 简单的行注释移除
            comment_pos = line.find('//')
            if comment_pos >= 0:
                line = line[:comment_pos]
            cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        # 移除块注释
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        return content
    
    def _extract_cells_optimized(self, content):
        
        
        # 使用更简单的方法找到cell块
        cell_starts = []
        cell_pattern = re.compile(r'cell\s*\(\s*([^)]+)\s*\)\s*{')
        
        # 找到所有cell的开始位置
        for match in cell_pattern.finditer(content):
            cell_starts.append((match.start(), match.end(), match.group(1).strip().strip('"')))
        
        print(f"find {len(cell_starts)} cells")
        
        if not cell_starts:
            print("warning: find 0 cell")
            return
        
        # 逐个解析cell
        for i, (start_pos, end_pos, cell_name) in enumerate(cell_starts):
            if self.debug_mode and i % 100 == 0:
                print(f"parsering number {i+1}/{len(cell_starts)} cell: {cell_name}")
            
            # 找到对应的结束大括号
            brace_count = 1
            pos = end_pos
            
            while pos < len(content) and brace_count > 0:
                char = content[pos]
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                pos += 1
            
            if brace_count == 0:
                cell_body = content[end_pos:pos-1]
                cell_info = self._parse_single_cell_optimized(cell_name, cell_body)
                self.cells[cell_name] = cell_info
            else:
                print(f"warning: can't find the end logo of {cell_name} ")
    
    def _parse_single_cell_optimized(self, cell_name, cell_body):
        
        
        cell_info = {
            'name': cell_name,
            'area': 0.0,
            'pins': {},
            'function': None,
            'timing_arcs': [],
            'power_info': {},
            'attributes': {}
        }
        
        # 提取面积 - 使用更简单的正则表达式
        area_match = re.search(r'area\s*:\s*([^;]+);', cell_body)
        if area_match:
            try:
                cell_info['area'] = float(area_match.group(1))
            except:
                cell_info['area'] = 0.0
        
        # 简化的pin提取
        pin_pattern = re.compile(r'pin\s*\(\s*([^)]+)\s*\)\s*{')
        pin_matches = list(pin_pattern.finditer(cell_body))
        
        for match in pin_matches:
            pin_name = match.group(1).strip().strip('"')
            # 简化的pin信息
            cell_info['pins'][pin_name] = {
                'name': pin_name,
                'direction': self._extract_simple_attribute(cell_body, 'direction', match.end()),
                'capacitance': 0.0,
                'timing': []
            }
        
        # 提取功能
        function_match = re.search(r'function\s*:\s*"([^"]+)"', cell_body)
        if function_match:
            cell_info['function'] = function_match.group(1)
        
        return cell_info
    
    def _extract_simple_attribute(self, content, attr_name, start_pos):
        
        # 在接下来的1000个字符内查找属性
        search_content = content[start_pos:start_pos+1000]
        pattern = fr'{attr_name}\s*:\s*([^;]+);'
        match = re.search(pattern, search_content)
        if match:
            return match.group(1).strip().strip('"')
        return None
    
    def _extract_library_info(self, content):
        
        
        # Extract library name
        lib_match = re.search(r'library\s*\(\s*([^)]+)\s*\)', content)
        if lib_match:
            self.library_info['name'] = lib_match.group(1).strip().strip('"')
        
        # Extract basic parameters
        basic_params = [
            'delay_model', 'nom_voltage', 'nom_temperature', 'nom_process',
            'default_max_transition', 'default_fanout_load'
        ]
        
        for param in basic_params:
            pattern = fr'{param}\s*:\s*([^;]+);'
            match = re.search(pattern, content)
            if match:
                value = match.group(1).strip().strip('"')
                try:
                    self.library_info[param] = float(value)
                except:
                    self.library_info[param] = value
    
    def _format_for_lib2vec(self):
        
        
        lib2vec_data = {
            'library_info': self.library_info,
            'cells': [],
            'statistics': {
                'total_cells': len(self.cells),
                'pin_count_distribution': defaultdict(int),
                'function_types': defaultdict(int)
            }
        }
        
        for cell_name, cell_info in self.cells.items():
            pin_count = len(cell_info['pins'])
            lib2vec_data['statistics']['pin_count_distribution'][pin_count] += 1
            
            if cell_info['function']:
                func_type = self._categorize_function(cell_info['function'])
                lib2vec_data['statistics']['function_types'][func_type] += 1
            
            formatted_cell = {
                'name': cell_name,
                'area': cell_info['area'],
                'pin_count': pin_count,
                'pins': list(cell_info['pins'].keys()),  # 简化pin信息
                'function': cell_info['function'],
                'cell_type': self._infer_cell_type(cell_name, cell_info)
            }
            
            lib2vec_data['cells'].append(formatted_cell)
        
        return lib2vec_data
    
    def _categorize_function(self, function):
        
        if not function:
            return 'unknown'
        
        function = function.lower()
        
        if 'and' in function:
            return 'and_gate'
        elif 'or' in function:
            return 'or_gate'
        elif 'not' in function or '!' in function:
            return 'inverter'
        elif 'xor' in function:
            return 'xor_gate'
        elif 'mux' in function:
            return 'multiplexer'
        elif 'latch' in function or 'dff' in function:
            return 'sequential'
        else:
            return 'combinational'
    
    def _infer_cell_type(self, cell_name, cell_info):
        
        name_lower = cell_name.lower()
        
        if 'and' in name_lower:
            return 'AND'
        elif 'or' in name_lower:
            return 'OR'
        elif 'inv' in name_lower or 'not' in name_lower:
            return 'INV'
        elif 'xor' in name_lower:
            return 'XOR'
        elif 'nand' in name_lower:
            return 'NAND'
        elif 'nor' in name_lower:
            return 'NOR'
        elif 'buf' in name_lower:
            return 'BUF'
        elif 'mux' in name_lower:
            return 'MUX'
        elif 'dff' in name_lower or 'latch' in name_lower:
            return 'SEQ'
        
        pin_count = len(cell_info['pins'])
        if pin_count <= 3:
            return 'BASIC'
        elif pin_count <= 6:
            return 'MEDIUM'
        else:
            return 'COMPLEX'
    
    def save_lib2vec_format(self, data, output_file):
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"data has saved to: {output_file}")

# 快速测试版本
def quick_test_parser(filename, max_cells=None):
    
    
    class QuickParser(OptimizedLib2VecLibertyParser):
        def _extract_cells_optimized(self, content):
            super()._extract_cells_optimized(content)
            if max_cells and len(self.cells) > max_cells:
                # 只保留前N个单元
                cell_items = list(self.cells.items())[:max_cells]
                self.cells = dict(cell_items)
                print(f"limit parser {max_cells} cells")
    
    parser = QuickParser()
    return parser.parse_liberty_file(filename)

# 使用示例
def main():
    # 首先尝试快速测试（只解析前10个单元）
    print("=== quick test mode ===")
    quick_data = quick_test_parser("/home/mingya/lib2vec-reproduction/data/asap7/asap7sc7p5t_27/LIB/NLDM/asap7sc7p5t_AO_LVT_TT_nldm_201020.lib", max_cells=10)
    
    if quick_data:
        print(f"successfulli! parser {quick_data['statistics']['total_cells']} cells")
        
        # 如果快速测试成功，询问是否继续完整解析
        print("\n=== full parser or not? ===")
        print("The quick test was successful. Would you like to perform the full test now?")
        
        # 完整解析
        parser = OptimizedLib2VecLibertyParser()
        data = parser.parse_liberty_file("/home/mingya/lib2vec-reproduction/data/asap7/asap7sc7p5t_27/LIB/NLDM/asap7sc7p5t_AO_LVT_TT_nldm_201020.lib")
        
        if data:
            parser.save_lib2vec_format(data, 'optimized_lib2vec_data.json')
            
            print("\n=== parser data ===")
            print(f"lib name: {data['library_info'].get('name', 'Unknown')}")
            print(f"total cell number: {data['statistics']['total_cells']}")
            print(f"nommal voltage: {data['library_info'].get('nom_voltage', 'Unknown')}V")

if __name__ == "__main__":
    main()
