#!/usr/bin/env python3
"""
从 Liberty 文件中提取 Lib2Vec 训练所需的数据
"""

import os
import sys
import json
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from liberty_parser import ASAP7LibertyParser

def extract_lib2vec_data(liberty_file_path, output_dir):
    """
    提取 Lib2Vec 所需的训练数据
    
    参数:
        liberty_file_path (str): Liberty 文件路径
        output_dir (str): 输出目录
    """
    os.makedirs(output_dir, exist_ok=True)
    
    parser = ASAP7LibertyParser(liberty_file_path)
    
    # 1. 提取功能表达式数据
    functional_data = {}
    expressions = parser.get_functional_expressions()
    
    for cell_name, expr in expressions.items():
        functional_data[cell_name] = {
            'expression': expr,
            'input_pins': [],
            'output_pins': []
        }
        
        # 获取单元的引脚信息
        cell_info = parser.get_cell_info(cell_name)
        for pin_name, pin_info in cell_info['pins'].items():
            if pin_info['direction'] == 'input':
                functional_data[cell_name]['input_pins'].append(pin_name)
            elif pin_info['direction'] == 'output':
                functional_data[cell_name]['output_pins'].append(pin_name)
    
    # 保存功能数据
    with open(os.path.join(output_dir, 'functional_data.json'), 'w') as f:
        json.dump(functional_data, f, indent=2)
    
    print(f"已提取 {len(functional_data)} 个单元的功能数据")
    
    # 2. 提取电气特性数据（采样）
    electrical_data = {}
    input_slew_range = []  # 输入转换时间范围
    output_load_range = []  # 输出负载范围
    
    # 首先确定所有单元的输入转换时间和输出负载范围
    for cell_name in parser.get_cell_names()[:10]:  # 只处理前10个单元以确定范围
        cell_info = parser.get_cell_info(cell_name)
        for arc in cell_info['timing_arcs']:
            if arc['cell_rise']:
                input_slew_range.extend(arc['cell_rise']['index_1'])
                output_load_range.extend(arc['cell_rise']['index_2'])
    
    # 确定采样范围（对数空间）
    input_slew_samples = np.logspace(
        np.log10(min(input_slew_range)), 
        np.log10(max(input_slew_range)), 
        150
    )
    output_load_samples = np.logspace(
        np.log10(min(output_load_range)), 
        np.log10(max(output_load_range)), 
        150
    )
    
    print(f"输入转换时间采样点: {len(input_slew_samples)}")
    print(f"输出负载采样点: {len(output_load_samples)}")
    
    # 保存采样配置
    sampling_config = {
        'input_slew_samples': input_slew_samples.tolist(),
        'output_load_samples': output_load_samples.tolist()
    }
    
    with open(os.path.join(output_dir, 'sampling_config.json'), 'w') as f:
        json.dump(sampling_config, f, indent=2)
    
    print("电气特性采样配置已保存")
    
    return {
        'functional_data': functional_data,
        'sampling_config': sampling_config
    }

if __name__ == "__main__":
    liberty_file_path = "data/asap7/LIBRARY/ASAP7.lib"
    output_dir = "data/processed"
    
    data = extract_lib2vec_data(liberty_file_path, output_dir)
    print("数据提取完成!")
