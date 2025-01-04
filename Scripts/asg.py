import boto3;

ec2_client = boto3.client('ec2')

# Create an AMI from the EC2 instance
image = ec2_client.create_image(InstanceId='i-0be9dbe4ff097d170', Name='sk-webAppImage')

# Create launch template using the AMI ID
launch_template = ec2_client.create_launch_template(
    LaunchTemplateName='sk-web-app-template',
    VersionDescription='v1',
    LaunchTemplateData={
        'ImageId': image['ImageId'],
        'InstanceType': 't2.micro',
        'SecurityGroupIds': ['sg-0034a5efe4d3dd625'],
        'KeyName': 'skauto'
    }
)

autoscaling = boto3.client('autoscaling')

#Create Auto Scaling Group (ASG)
response = autoscaling.create_auto_scaling_group(
    AutoScalingGroupName='sk-auto-scaling-group',
    LaunchTemplate={'LaunchTemplateName':'sk-web-app-template','Version':'1'},
    MinSize=1,
    MaxSize=5,
    DesiredCapacity=2,
    VPCZoneIdentifier='subnet-01874c4512136bd62',
    TargetGroupARNs=['arn:aws:elasticloadbalancing:us-east-1:975050024946:targetgroup/SkMernTravelMemory/ee0bb9a6a36066eb']
)

# Create scaling policy based on CPU utilization
autoscaling.put_scaling_policy(
    AutoScalingGroupName='sk-auto-scaling-group',
    PolicyName='scale-out-policy',
    ScalingAdjustment=1,
    AdjustmentType='ChangeInCapacity',
    Cooldown=300,
    MetricAggregationType='Average',
    EstimatedInstanceWarmup=300,
    StepAdjustments=[{
        'MetricIntervalLowerBound': 0,
        'ScalingAdjustment': 1
    }]
)    