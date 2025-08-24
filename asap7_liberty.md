# asap7sc7p5t_AO_LVT_TT_nldm_201020.lib为例
1. Liberty 文件整体架构

Liberty 文件是 层次化的 block–attribute 结构，可以看作是树状数据：
```Liberty
library (<库名>) {
    attribute ...
    attribute ...
    
    cell (<单元名>) {
        attribute ...
        pin (<引脚名>) {
            attribute ...
            timing() { ... }
            internal_power() { ... }
        }
    }
}
```

关键层级：

library：最外层，定义整个工艺库的范围、工艺条件、单位等。

cell：一个具体的标准单元（如 AOI21、NAND2、INV 等）。

pin：单元上的引脚定义（输入/输出/电源引脚）。

timing/power：在 pin 下，描述时序延迟、建立保持时间、功耗信息。

2. 典型结构展开
(1) Library 头部
```liberty
library (asap7sc7p5t_AO_LVT_TT_nldm_201020) {
    technology ("cmos");
    delay_model : table_lookup;
    time_unit : "1ns";
    voltage_unit : "1V";
    current_unit : "1uA";
    pulling_resistance_unit : "1kohm";
    leakage_power_unit : "1nW";
    capacitive_load_unit (1,pf);
    ...
}
```

解释：

technology：库的工艺类型。

delay_model：延迟建模方式，ASAP7 用 table_lookup。

time_unit / voltage_unit 等：单位定义。

capacitive_load_unit：负载电容单位。

这些是 全局设定，影响下面 cell 的解释。

(2) Cell 定义
```liberty
cell (AOI21xp33_ASAP7_75t_L) {
    area : 1.44;
    cell_leakage_power : 0.0012;

    pin(A) {
        direction : input;
        capacitance : 0.0021;
        rise_capacitance : 0.0020;
        fall_capacitance : 0.0022;
    }

    pin(Y) {
        direction : output;
        function : "!(A & B + C)";
        max_capacitance : 0.05;
        timing() {
            related_pin : "A";
            timing_sense : negative_unate;
            cell_rise (...) { values(...); }
            rise_transition (...) { values(...); }
            cell_fall (...) { values(...); }
            fall_transition (...) { values(...); }
        }
    }
}
```

解释：

cell：一个逻辑门（例子是 AOI21）。

area：标准单元面积（影响布局布线工具优化）。

cell_leakage_power：静态漏电功耗。

pin(A)：输入引脚，定义方向、输入电容。

pin(Y)：输出引脚，定义逻辑功能 (function)、最大负载电容、以及和输入之间的时序关系。

(3) Timing 块
```liberty
timing() {
    related_pin : "A";
    timing_sense : negative_unate;
    cell_rise (template) { values("..."); }
    cell_fall (template) { values("..."); }
    rise_transition (template) { values("..."); }
    fall_transition (template) { values("..."); }
}
```

解释：

related_pin：这个延迟是相对于哪个输入引脚的。

timing_sense：延迟的单调性

positive_unate：输入上升 → 输出上升

negative_unate：输入上升 → 输出下降

non_unate：无法确定单调性（如 XOR）。

cell_rise/cell_fall：上升/下降延迟查找表。

rise_transition/fall_transition：输出转换时间查找表。

这些查表数据是 二维 LUT，横纵坐标一般是输入转换时间 (input slew) 和输出负载电容 (output load)，表值是延迟/转换。

(4) 功耗建模
```liberty
internal_power() {
    related_pin : "A";
    rise_power(template) { values(...); }
    fall_power(template) { values(...); }
}
```

解释：

功耗表和时序表类似，也是 lookup table。

rise_power / fall_power：当输入翻转时的动态功耗。

3. ASAP7 的特点

ASAP7 的 .lib 文件相比传统 65nm/28nm 工艺更细：

单元命名包含电压阈值（HVT/LVT）、工艺角（TT）、延迟模型类型（nldm）。

更小的面积值，符合 7nm FinFET 工艺。

LUT 表格一般更稠密，因为高频特性敏感。

4. 总结结构树

用一个树状图总结：
```bash
library
 ├── 全局参数 (单位、delay_model 等)
 ├── cell (INV, NAND2, AOI21, ...)
 │    ├── area, leakage_power
 │    ├── pin (输入)
 │    │    └── capacitance
 │    └── pin (输出)
 │         ├── function
 │         ├── timing
 │         │    ├── related_pin
 │         │    ├── timing_sense
 │         │    ├── cell_rise/fall
 │         │    └── transition
 │         └── internal_power
 └── ...
 ```

# Liberty文件片段详细解释

## 1. 电压映射 (Voltage Mapping)
```
voltage_map (VDD, 0.7);   # 定义VDD为0.7V
voltage_map (VSS, 0);     # 定义VSS为0V
voltage_map (GND, 0);     # 定义GND为0V
```
定义了电源网络的电压值，VDD是正电源，VSS和GND是接地。

## 2. 默认参数设置
```
default_cell_leakage_power : 0;        # 默认单元泄漏功耗为0
default_fanout_load : 1;               # 默认扇出负载为1
default_max_transition : 320;          # 默认最大转换时间320ps
default_output_pin_cap : 0;            # 默认输出引脚电容为0
```

## 3. 阈值设置
```
input_threshold_pct_fall : 50;         # 输入下降阈值为50%
input_threshold_pct_rise : 50;         # 输入上升阈值为50%
output_threshold_pct_fall : 50;        # 输出下降阈值为50%
output_threshold_pct_rise : 50;        # 输出上升阈值为50%
```
定义了逻辑0/1的判断阈值，50%表示在VDD/2处判断逻辑电平。

## 4. 工艺条件
```
nom_process : 1;           # 标准工艺条件
nom_temperature : 25;      # 标准温度25°C
nom_voltage : 0.7;         # 标准电压0.7V

operating_conditions (PVT_0P7V_25C) {
    process : 1;           # 工艺参数
    temperature : 25;      # 温度25°C
    voltage : 0.7;         # 电压0.7V
}
```
PVT表示Process-Voltage-Temperature，定义了标准的工艺、电压、温度条件。

## 5. 转换速率设置
```
slew_derate_from_library : 1;          # 转换速率降额系数
slew_lower_threshold_pct_fall : 10;    # 下降沿下阈值10%
slew_lower_threshold_pct_rise : 10;    # 上升沿下阈值10%
slew_upper_threshold_pct_fall : 90;    # 下降沿上阈值90%
slew_upper_threshold_pct_rise : 90;    # 上升沿上阈值90%
```
定义了计算转换时间的测量点，通常在10%~90%之间测量。

## 6. 查找表模板 (Lookup Table Templates)

### 约束模板 (7x7)
```
lu_table_template (constraint_template_7x7) {
    variable_1 : constrained_pin_transition;    # 受约束引脚的转换时间
    variable_2 : related_pin_transition;        # 相关引脚的转换时间
    index_1 ("5, 10, 20, 40, 80, 160, 320");   # 第一维索引(ps)
    index_2 ("5, 10, 20, 40, 80, 160, 320");   # 第二维索引(ps)
}
```

### 延迟模板 (7x7)
```
lu_table_template (delay_template_7x7_x1) {
    variable_1 : input_net_transition;          # 输入网络转换时间
    variable_2 : total_output_net_capacitance;  # 输出网络总电容
    index_1 ("5, 10, 20, 40, 80, 160, 320");   # 转换时间索引(ps)
    index_2 ("0.72, 1.44, 2.88, 5.76, 11.52, 23.04, 46.08"); # 电容索引(fF)
}
```

### 功耗模板
```
power_template_7x7_x1: 用于动态功耗计算
passive_power_template_7x1_x1: 用于静态功耗计算
```

## 7. 电压规格
```
input_voltage (default_VDD_VSS_input) {
    vil : 0;        # 输入低电平最大值
    vih : 0.7;      # 输入高电平最小值
    vimin : 0;      # 输入电压最小值
    vimax : 0.7;    # 输入电压最大值
}

output_voltage (default_VDD_VSS_output) {
    vol : 0;        # 输出低电平最大值
    voh : 0.7;      # 输出高电平最小值
    vomin : 0;      # 输出电压最小值
    vomax : 0.7;    # 输出电压最大值
}
```

## 8. 波形模板
```
normalized_driver_waveform (waveform_template_name) {
    driver_waveform_name : "PreDriver20.5:rise";   # 驱动器波形名称
    index_1: 7个转换时间点 (5-320ps)
    index_2: 17个归一化电压点 (0-1)
    values: 7x17的波形数据矩阵
}
```

这个波形数据描述了在不同输入转换时间下，输出信号的标准化上升波形。每行对应一个输入转换时间，每列对应一个归一化电压点的时间值。
