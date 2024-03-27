#!/bin/bash
# 检查并安装 Git
if ! command -v git &>/dev/null; then
  echo "Git is not installed. Installing Git..."
  apt-get update
  apt-get install -y git
fi

# 检查并克隆 GitHub 仓库
if [ ! -d "MonitorGpu" ]; then
  echo "Cloning GitHub repository..."
  git clone -b master https://github.com/nimysan/MonitorGpu.git
  cd MonitorGpu
else
  cd MonitorGpu
fi
# 检查并安装依赖库
if ! python3 -c "import pynvml, boto3" 2>/dev/null; then
  echo "Installing required libraries..."
  pip install pynvml boto3
fi
# 检查进程是否存在
PIDS=`ps -ef | grep GpuMonitor | awk '{print $2}'`
for pid in $PIDS
do
  kill -9 $pid
done
echo "exist process ${PIDS}"
echo "Starting GpuMonitor.py in the background..."
nohup python3 ./GpuMonitor.py >/var/log/ssm-gpumonitor.log 2>&1 &
