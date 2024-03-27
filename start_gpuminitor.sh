#!/bin/bash

# 检查并安装依赖库
if ! python -c "import pynvml, boto3" 2>/dev/null; then
    echo "Installing required libraries..."
    pip install pynvml boto3 -y
fi
# 检查进程是否存在
if pgrep -x "GpuMonitor.py" > /dev/null
then
    echo "GpuMonitor.py is already running."
else
    echo "Starting GpuMonitor.py in the background..."
    nohup python /path/to/GpuMonitor.py > /var/logs/gpumonitor.log 2>&1 &
fi
