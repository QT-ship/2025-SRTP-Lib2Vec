#!/bin/bash
echo "设置Lib2Vec复现环境..."

# 加载 conda
source /home/mingya/program_sources/miniconda3/etc/profile.d/conda.sh

# 激活外层 Conda 环境
if conda env list | grep -q "Lib2Vec"; then
    echo "激活 Conda 环境 Lib2Vec..."
    conda activate Lib2Vec
else
    echo "Conda 环境 Lib2Vec 不存在"
    return 1
fi

cd ..

# 激活内层 Python venv
if [ -d "Lib2Vec-env" ]; then
    echo "激活 Python venv Lib2Vec-env..."
    source Lib2Vec-env/bin/activate
else
    echo "Python venv Lib2Vec-env 不存在"
    return 1
fi

# 检查CUDA驱动
if ! command -v nvidia-smi &> /dev/null; then
    echo "错误: 未找到NVIDIA驱动"
    return 1
fi

# 设置CUDA路径
export CUDA_HOME=/usr/local/cuda-11.8
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# 检查Python包
echo "检查Python包..."
python3 -c "
import torch, numpy as np, pandas as pd
print(f'PyTorch版本: {torch.__version__}')
print(f'CUDA可用: {torch.cuda.is_available()}')
print(f'NumPy: {np.__version__}')
print(f'Pandas: {pd.__version__}')
"

echo "环境设置完成!"
echo "当前Conda环境: $(conda info --envs | grep '*')"
echo "当前Python路径: $(which python)"

