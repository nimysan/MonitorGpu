import boto3
topic_arn = "arn:aws:sns:us-east-1:xxxx:gpu-monitor-alarm"
aws_region = 'us-east-1'

# 创建 CloudWatch 客户端
cloudwatch = boto3.client('cloudwatch', region_name=aws_region)

# 获取所有 EC2 实例
ec2 = boto3.resource('ec2', region_name=aws_region)
instances = ec2.instances.all()


def metric_exist(instance_id):
    # 检查是否存在 GPU 指标
    resp = cloudwatch.list_metrics(
        Namespace='GPU',
        MetricName='gpu_0_encoder_util',
        Dimensions=[
            {
                'Name': 'InstanceId',
                'Value': instance_id
            },
        ]
    )
    # print(response)

    return len(resp["Metrics"]) > 0;


# 为每个 EC2 实例设置 CPU 利用率监控
for instance in instances:
    instance_id = instance.id

    # 检查是否已经存在警报
    try:
        if not metric_exist(instance_id):
            print(f"no alaram for {instance_id}")
            continue
        Threshold = 30;
        cloudwatch.put_metric_alarm(
            AlarmName=f'GPU Encode Utilization - {instance_id}',
            ComparisonOperator='LessThanThreshold',
            EvaluationPeriods=3,
            MetricName='gpu_0_encoder_util',
            Namespace='GPU',
            Period=60,
            Statistic='Average',
            Threshold=Threshold,
            ActionsEnabled=False,
            AlarmDescription=f'Alarm when GPU encoder utilization less than {Threshold}% for {instance_id}',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                },
            ],
            AlarmActions=[topic_arn]
        )
        print(f"create alarm for {instance_id}")
    except cloudwatch.exceptions.ResourceNotFoundException:
        print("exception")
