#!/usr/bin/env python3
"""
测试 Liberty 文件解析器
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

print("Python path:")
for path in sys.path:
    print(f"  {path}")

from liberty_parser import ASAP7LibertyParser

def main():
    # 替换为您的 Liberty 文件路径
    liberty_file_path = "data/asap7/LIBRARY/ASAP7.lib"
    
    try:
        # 创建解析器实例
        parser = ASAP7LibertyParser(liberty_file_path)
        
        print("=" * 50)
        print("Liberty 文件解析测试")
        print("=" * 50)
        
        # 获取基本信息
        cell_names = parser.get_cell_names()
        cell_count = parser.get_cell_count()
        
        print(f"找到 {cell_count} 个单元")
        print(f"前10个单元: {cell_names[:10]}")
        print()
        
        # 获取几个示例单元的详细信息
        sample_cells = cell_names[:3]  # 测试前3个单元
        
        for cell_name in sample_cells:
            print(f"解析单元: {cell_name}")
            cell_info = parser.get_cell_info(cell_name)
            
            print(f"  引脚数量: {len(cell_info['pins'])}")
            print(f"  功能表达式: {cell_info.get('functions', {})}")
            print(f"  时序弧数量: {len(cell_info['timing_arcs'])}")
            
            # 打印一个时序弧的详细信息（如果有）
            if cell_info['timing_arcs']:
                arc = cell_info['timing_arcs'][0]
                print(f"  示例时序弧: {arc['from_pin']} -> {arc['to_pin']}")
                if arc['cell_rise']:
                    print(f"    上升延迟查找表维度: {len(arc['cell_rise']['index_1'])}x{len(arc['cell_rise']['index_2'])}")
            print()
        
        # 测试功能表达式查找
        print("查找功能表达式包含 '&' 的单元 (AND类型):")
        and_cells = parser.find_cells_by_function('&')
        print(f"找到 {len(and_cells)} 个AND类型单元: {and_cells[:5]}{'...' if len(and_cells) > 5 else ''}")
        print()
        
        print("查找功能表达式包含 '|' 的单元 (OR类型):")
        or_cells = parser.find_cells_by_function('|')
        print(f"找到 {len(or_cells)} 个OR类型单元: {or_cells[:5]}{'...' if len(or_cells) > 5 else ''}")
        print()
        
        print("测试完成! 解析器工作正常。")
        
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请确保 Liberty 文件路径正确")
    except Exception as e:
        print(f"解析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
