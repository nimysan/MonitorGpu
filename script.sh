#!/bin/bash

apt-get install -y python3-pip
# 检查并安装 Git
if ! command -v git &>/dev/null; then
  echo "Git is not installed. Installing Git..."
  apt-get update

#  apt install python3-pip
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
pip install pynvml boto3
# 检查进程是否存在
PIDS=`ps -ef | grep GpuMonitor| grep -v "grep" | awk '{print $2}'`
for pid in $PIDS
do
  kill -9 $pid
done
echo "exist process ${PIDS}"
echo "Starting GpuMonitor.py in the background..."
nohup python3 ./GpuMonitor.py >> /var/log/ssm-gpumonitor.log 2>&1 &
