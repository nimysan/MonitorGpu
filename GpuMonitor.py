"""
nvidia-smi dmon -i 0

# gpu   pwr gtemp mtemp    sm   mem   enc   dec  mclk  pclk
# Idx     W     C     C     %     %     %     %   MHz   MHz
    0     62     27      -     7      1    100      5   6250   1710
    0     63     27      -     8      2    100      4   6250   1710
    0     63     27      -     8      2    100      4   6250   1710
    0     63     27      -     8      2    100      4   6250   1710
    0     62     27      -     7      1    100      4   6250   1710
    0     62     27      -     7      1    100      4   6250   1710
    0     63     27      -     7      1    100      4   6250   1710
    0     63     27      -     7      2    100      4   6250   1710
    0     63     27      -     7      1    100      4   6250   1710
    0     62     27      -     7      1    100      4   6250   1710
    0     63     27      -     7      1    100      4   6250   1710

1. `# gpu`: GPU 索引号
2. `pwr`: GPU 功耗, 单位 W
3. `gtemp`: GPU 温度, 单位 ℃
4. `mtemp`: 内存温度, 单位 ℃ (有些 GPU 没有这个指标)
5. `sm`: GPU 处理器利用率, 单位 %
6. `mem`: GPU 内存利用率, 单位 %
7. `enc`: GPU 编码利用率, 单位 %
8. `dec`: GPU 解码利用率, 单位 %
9. `mclk`: GPU 内存时钟频率, 单位 MHz
10. `pclk`: GPU 处理器时钟频率, 单位 MHz
"""

import os
import time
import boto3
from pynvml import *
import requests

# 初始化 NVML
nvmlInit()

# 获取 GPU 设备数量
device_count = nvmlDeviceGetCount()

# 定义需要上报的指标
METRICS = [
    'gpu_utilization',
    'gpu_memory_used',
    'gpu_temperature',
    'gpu_power_usage',
]


def get_current_region():
    """
    Retrieves the AWS Region of the current EC2 instance.

    Returns:
        str: The name of the AWS Region where the current EC2 instance is located.
    """
    # Create an EC2 client
    ec2 = boto3.client('ec2')

    # Describe the availability zones
    response = ec2.describe_availability_zones()

    # Extract the Region name from the response
    region = response['AvailabilityZones'][0]['RegionName']

    return region


# 定义 CloudWatch 客户端
cw = boto3.client('cloudwatch', region_name="us-east-1")


def collect_gpu_metrics():
    """收集 GPU 指标"""
    gpu_metrics = {}
    for i in range(device_count):
        handle = nvmlDeviceGetHandleByIndex(i)
        # total_memory = nvmlDeviceGetMemoryInfo(i).total
        # print(handle)
        gpu_metrics[f'gpu_{i}_utilization'] = nvmlDeviceGetUtilizationRates(handle).gpu
        mem = nvmlDeviceGetMemoryInfo(handle)
        used = mem.used
        total = mem.total
        gpu_metrics[f'gpu_{i}_memory_used'] = used
        gpu_metrics[f'gpu_{i}_memory_utilization'] = used / total * 100
        gpu_metrics[f'gpu_{i}_temperature'] = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
        gpu_metrics[f'gpu_{i}_power_usage'] = nvmlDeviceGetPowerUsage(handle) / 1000.0  # 转换为瓦特
        # 获取 GPU encoder/decoder 利用率
        enc_util, test = nvmlDeviceGetEncoderUtilization(handle)
        gpu_metrics[f'gpu_{i}_encoder_util'] = enc_util

        dec_util, test1 = nvmlDeviceGetDecoderUtilization(handle)
        gpu_metrics[f'gpu_{i}_decoder_util'] = dec_util

    # print(gpu_metrics)
    return gpu_metrics


def put_metrics_to_cloudwatch(gpu_metrics, instance_id):
    """将 GPU 指标上报到 CloudWatch"""
    namespace = 'GPU'
    timestamp = time.time()
    metric_data = []
    for metric_name, metric_value in gpu_metrics.items():
        metric_data.append({
            'MetricName': metric_name,
            'Value': metric_value,
            'Unit': 'None',
            'Timestamp': timestamp,
            'Dimensions': [
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                }
            ]
        })
    if metric_data:
        resp = cw.put_metric_data(Namespace=namespace, MetricData=metric_data)
        # print(resp)
    else:
        print("no data")


def get_instance_id():
    """获取当前实例的 instanceID"""
    try:
        response = requests.get('http://169.254.169.254/latest/dynamic/instance-identity/document')
        instance_id = response.json()['instanceId']
        return instance_id
    except Exception as e:
        print(f"Error getting instance ID: {e}")
        return None


def main():
    instance_id = get_instance_id()
    while True:
        gpu_metrics = collect_gpu_metrics()
        put_metrics_to_cloudwatch(gpu_metrics, instance_id)
        time.sleep(5)  # 每分钟收集和上报一次指标
        print("run")


if __name__ == '__main__':
    main()
