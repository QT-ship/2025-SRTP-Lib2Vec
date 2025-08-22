import os
from liberty.parser import LibertyParser

class ASAP7LibertyParser:
    """
    使用 liberty-parser 0.0.25 库解析 ASAP7 Liberty 文件的类
    提取 Lib2Vec 所需的功能和电气特性信息
    """
    
    def __init__(self, liberty_file_path):
        """
        初始化解析器
        
        参数:
            liberty_file_path (str): Liberty 文件的路径
        """
        if not os.path.exists(liberty_file_path):
            raise FileNotFoundError(f"Liberty 文件不存在: {liberty_file_path}")
        
        self.liberty_file_path = liberty_file_path
        self._parser = LibertyParser(open(liberty_file_path, 'r'))
        self.library = self._parser.parse()
    
    def get_cell_names(self):
        """获取库中所有单元的名称列表"""
        return [cell.name for cell in self.library.get_groups('cell')]
    
    def get_cell_count(self):
        """获取库中单元的数量"""
        return len(self.get_cell_names())
    
    def get_cell_info(self, cell_name):
        """
        获取指定单元的详细信息
        
        参数:
            cell_name (str): 单元名称
            
        返回:
            dict: 包含单元信息的字典
        """
        cell = self.library.get_group('cell', cell_name)
        if not cell:
            raise ValueError(f"找不到单元: {cell_name}")
        
        # 提取单元基本信息
        cell_info = {
            'name': cell.name,
            'pins': {},
            'functions': {},
            'timing_arcs': []
        }
        
        # 提取引脚信息
        for pin in cell.get_groups('pin'):
            pin_name = pin.args[0] if pin.args else None
            if pin_name:
                pin_info = {
                    'direction': pin.get_string('direction'),
                    'function': pin.get_string('function'),
                    'capacitance': pin.get_value('capacitance') if pin.get_value('capacitance') else 0.0
                }
                cell_info['pins'][pin_name] = pin_info
                
                # 记录输出引脚的功能表达式
                if pin_info['direction'] == 'output' and pin_info['function']:
                    cell_info['functions'][pin_name] = pin_info['function']
        
        # 提取时序弧信息
        for pin in cell.get_groups('pin'):
            if pin.get_string('direction') == 'output':
                pin_name = pin.args[0] if pin.args else None
                if pin_name:
                    for timing in pin.get_groups('timing'):
                        related_pin = timing.get_string('related_pin')
                        if related_pin:
                            # 提取时序弧的电气特性
                            timing_arc = {
                                'from_pin': related_pin,
                                'to_pin': pin_name,
                                'cell_rise': self._extract_lut_data(timing, 'cell_rise'),
                                'cell_fall': self._extract_lut_data(timing, 'cell_fall'),
                                'rise_transition': self._extract_lut_data(timing, 'rise_transition'),
                                'fall_transition': self._extract_lut_data(timing, 'fall_transition'),
                                'rise_power': self._extract_lut_data(timing, 'rise_power'),
                                'fall_power': self._extract_lut_data(timing, 'fall_power')
                            }
                            cell_info['timing_arcs'].append(timing_arc)
        
        return cell_info
    
    def _extract_lut_data(self, timing_group, lut_name):
        """
        提取查找表数据
        
        参数:
            timing_group: 时序组
            lut_name (str): 查找表名称
            
        返回:
            dict: 包含查找表索引和值的字典
        """
        lut_group = timing_group.get_group(lut_name)
        if not lut_group:
            return None
        
        lut_data = {
            'index_1': lut_group.get_array('index_1'),  # 输入转换时间
            'index_2': lut_group.get_array('index_2'),  # 输出负载
            'values': lut_group.get_array('values')     # 对应的值矩阵
        }
        
        return lut_data
    
    def get_all_cells_info(self):
        """
        获取库中所有单元的详细信息
        
        返回:
            dict: 以单元名称为键，单元信息为值的字典
        """
        all_cells = {}
        for cell_name in self.get_cell_names():
            try:
                all_cells[cell_name] = self.get_cell_info(cell_name)
            except Exception as e:
                print(f"解析单元 {cell_name} 时出错: {e}")
        
        return all_cells
    
    def get_functional_expressions(self):
        """
        获取所有单元的功能表达式
        
        返回:
            dict: 以单元名称为键，功能表达式为值的字典
        """
        expressions = {}
        for cell_name in self.get_cell_names():
            cell_info = self.get_cell_info(cell_name)
            for pin_name, pin_info in cell_info['pins'].items():
                if pin_info['direction'] == 'output' and pin_info.get('function'):
                    expressions[cell_name] = pin_info['function']
                    break  # 只取第一个输出引脚的功能
        
        return expressions
    
    def find_cells_by_function(self, function_pattern):
        """
        根据功能表达式查找单元
        
        参数:
            function_pattern (str): 功能表达式模式
            
        返回:
            list: 匹配的单元名称列表
        """
        matched_cells = []
        expressions = self.get_functional_expressions()
        
        for cell_name, expr in expressions.items():
            if function_pattern in expr:
                matched_cells.append(cell_name)
        
        return matched_cells
