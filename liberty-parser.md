# 基本用法

导入并解析 Liberty 文件：

from liberty.parser import parse_liberty

## 读取并解析 Liberty 文件
with open("path_to_liberty_file.lib", "r") as f:
    library = parse_liberty(f.read())

## 打印解析后的库结构
print(str(library))


解析后的 library 是一个包含多个 Group 对象的结构，代表 Liberty 文件中的各个组。

# 访问组和属性

Liberty 文件由三种主要结构组成：

Group：代表一个命名的组，可能包含其他组或属性。

Simple Attribute：简单属性，格式为 name: value;。

Complex Attribute：复杂属性，格式为 name (param1, param2, ...);。
GitHub
+2
GitHub
+2

访问特定组和属性的示例：
emsec.github.io

## 获取所有名为 'cell' 的组
for cell_group in library.get_groups('cell'):
    print(f"Cell Name: {cell_group.args[0]}")

    # 获取该组下所有名为 'pin' 的子组
    for pin_group in cell_group.get_groups('pin'):
        print(f"  Pin Name: {pin_group.args[0]}")

        # 访问特定属性
        if 'area' in pin_group:
            print(f"    Area: {pin_group['area']}")


get_groups 方法用于获取指定名称的子组，args 属性返回组的参数列表，[] 用于访问属性值。
PyPI

# 处理数组和时序表

Liberty 文件中的复杂属性，如时序表，通常存储为逗号分隔的字符串。可以使用 get_array 方法将其转换为 NumPy 数组：
PyPI

import numpy as np

## 获取名为 'timing' 的属性，并转换为 NumPy 数组
timing_data = pin_group.get_array('timing')
print(np.array(timing_data))


这对于进一步的时序分析和建模非常有用。
Strumenta
+1

# 测试和示例

库提供了测试文件 tests.py，可以用于验证解析功能：

python liberty/tests.py


此外，示例脚本位于 ./examples 目录，可供参考。
PyPI

# 保存和加载库

可以使用 load_liberty 和 save_liberty 函数加载和保存 Liberty 文件：

from liberty.parser import load_liberty, save_liberty

## 加载 Liberty 文件
library = load_liberty("original.lib")

## 保存为新文件
save_liberty(library, "modified.lib")


这对于修改和更新标准单元库非常有用。

# 结构和语法概览

Liberty 格式的基本语法：

Group 语句：group_type (group_name) { ... }

简单属性：attribute_name: value;

复杂属性：attribute_name (param1, param2, ...);
GitHub
+1
GitHub
+1

这些结构用于描述标准单元的各个方面，如时序、功耗、引脚类型等。