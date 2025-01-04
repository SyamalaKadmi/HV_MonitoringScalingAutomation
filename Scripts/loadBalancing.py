import boto3;

elbv2 = boto3.client('elbv2')

# Create a load balancer
response = elbv2.create_load_balancer(
    Name='sk-web-app-alb',
    Subnets=['subnet-01874c4512136bd62','subnet-08fa616f96d54dfc2'],  
    SecurityGroups=['sg-0034a5efe4d3dd625'],
    Scheme='internet-facing',
    Type='application'
)

alb_arn = response['LoadBalancers'][0]['LoadBalancerArn']

# Create a target group for the EC2 instance
target_group = elbv2.create_target_group(
    Name='SkMernTravelMemory',
    Protocol='HTTP',
    Port=80,
    VpcId='vpc-09f02049d6176fe30'
)

# Register EC2 instance in the target group
instance_id = 'i-0be9dbe4ff097d170'
elbv2.register_targets(
    TargetGroupArn=target_group['TargetGroups'][0]['TargetGroupArn'],
    Targets=[{'Id': instance_id}]
)

# Create a listener for the ALB to forward traffic to the target group
elbv2.create_listener(
    LoadBalancerArn=alb_arn,
    Protocol='HTTP',
    Port=80,
    DefaultActions=[{
        'Type': 'forward',
        'TargetGroupArn': target_group['TargetGroups'][0]['TargetGroupArn']
    }]
)
