import boto3

# Initialize S3,ec2 client
s3 = boto3.client('s3')
ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')
autoscaling = boto3.client('autoscaling')
sns_client = boto3.client('sns', region_name='us-east-1')  # Set your AWS region
lambda_client = boto3.client('lambda', region_name='us-east-1')  # For Lambda integration

# Define Bucket Name
bucket_name = 'sk-web-app-static-files-bucket'

# Define SNS Topic names
topics = {
    "sk-Health-Issues-Alert": "Health issues in your infrastructure",
    "sk-Scaling-Event-Alert": "Scaling events for your infrastructure",
    "sk-High-Traffic-Alert": "High traffic alert in your application"
}

# Define ASG
AutoScalingGroupName='sk-auto-scaling-group'

# Create the S3 bucket
def create_bucket(bucketname):
    s3.create_bucket(Bucket=bucket_name)
    # Upload static files to S3
    s3.upload_file('./HeroViredRepositories/templates/calculator.html', bucket_name, 'calculator.html')

#Launch EC2 instance
def create_instance():
    instance = ec2.create_instances(
        ImageId='ami-01816d07b1128cd2d',
        InstanceType='t2.micro',
        KeyName='skauto',
        SubnetId='subnet-01874c4512136bd62',
        SecurityGroupIds=['sg-0034a5efe4d3dd625'],
        MinCount=1,
        MaxCount=1,
    
        UserData="""#!/bin/bash
                    sudo yum update -y
                    sudo yum install git -y
                    sudo yum install python3 -y
                    sudo yum install python3-pip
                    sudo pip3 install flask
                    sudo python3 -m pip install gunicorn
                    sudo yum install -y nginx
                    sudo systemctl start nginx
                    sudo systemctl enable nginx
                    sudo git clone https://github.com/SyamalaKadmi/HeroViredRepositories.git /home/flask_app
                    sudo cd /home/flask_app
                    sudo python3 app.py"""
    )
    #Wait for instance to be in running state
    instance[0].wait_until_running()
 
instance_id=instance.id

# Deploy LoadBalancer
def create_loadbalancer():
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
 
# Create Auto Scaling Group
def create_asg():
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

    #Create Auto Scaling Group (ASG)
    response = autoscaling.create_auto_scaling_group(
        AutoScalingGroupName='sk-auto-scaling-group',
        LaunchTemplate={'LaunchTemplateName':'sk-web-app-template','Version':'1'},
        MinSize=1,
        MaxSize=5,
        DesiredCapacity=2,
        VPCZoneIdentifier='subnet-01874c4512136bd62',
        TargetGroupARNs=[TargetGroupArn]
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

# Setup Lambda & SNS notifications
def sns_lambdaSetup():
    # Function to create SNS topic and return its ARN
    def create_sns_topic(topic_name):
        try:
            response = sns_client.create_topic(Name=topic_name)
            topic_arn = response['TopicArn']
            print(f"Created SNS topic '{topic_name}' with ARN: {topic_arn}")
            return topic_arn
        except Exception as e:
            print(f"Error creating SNS topic: {str(e)}")
            return None

    # Function to subscribe administrators to SNS topic via email or SMS
    def subscribe_to_sns(topic_arn, protocol, endpoint):
        try:
            response = sns_client.subscribe(
                TopicArn=topic_arn,
                Protocol=protocol,
                Endpoint=endpoint
            )
            print(f"Subscribed {endpoint} to {topic_arn} via {protocol}")
            return response
        except Exception as e:
            print(f"Error subscribing to SNS topic: {str(e)}")
            return None

    # Function to create a Lambda function to handle notifications and trigger SNS
    def create_lambda_function():
        lambda_code = """
                        import json
                        import boto3

                        sns_client = boto3.client('sns')

                        def lambda_handler(event, context):
                            # Get SNS Topic ARN from the event or hardcoded
                            topic_arns = {'arn:aws:sns:us-east-1:975050024946:sk-Health-Issues-Alert', 'arn:aws:sns:us-east-1:975050024946:sk-High-Traffic-Alert', 'arn:aws:sns:us-east-1:975050024946:sk-Scaling-Event-Alert
                            for topic in topic_arns:
                                topic_arn = event.get('TopicArn', topic)
                                message = json.dumps(event)  # Simple message formatting
                                subject = "Health Issues Event Notification"
    
                                # Publish to SNS topic
                                response = sns_client.publish(
                                TopicArn=topic_arn,
                                Message=message,
                                Subject=subject
                                )
    
                            print(f"Notification sent with response: {response}")
                            return response
                        """
        # Lambda role needs permission to publish to SNS
        role_arn = "arn:aws:iam::975050024946:role/sk_automation_"  
    
        try:
            response = lambda_client.create_function(
                FunctionName='sk_applifecycle_automation',
                Runtime='python3.8',
                Role=role_arn,
                Handler='index.lambda_handler',
                Code={'ZipFile': lambda_code.encode()},
                Timeout=60
            )
            print(f"Lambda function 'sk_applifecycle_automation' created: {response}")
            return response
        except Exception as e:
            print(f"Error creating Lambda function: {str(e)}")
            return None

    # Main function to orchestrate the process
    def setup_notifications():
        # Create SNS topics
        topic_arns = {}
        for topic_name in topics:
            topic_arn = create_sns_topic(topic_name)
            if topic_arn:
                topic_arns[topic_name] = topic_arn
    
        # Subscribe admins to the topics
        subscribe_to_sns(topic_arns["sk-Health-Issues-Alert"], 'email', 'syamala.kadimi@gmail.com')
        subscribe_to_sns(topic_arns["sk-Scaling-Event-Alert"], 'sms', '+919284018836')  # Example for SMS
        subscribe_to_sns(topic_arns["sk-High-Traffic-Alert"], 'email', 'syamala.kadimi@gmail.com')
    
        # Create Lambda function to handle SNS triggers
        create_lambda_function()
    setup_notifications()

def deploy_infrastructure():
    # Deploy S3, EC2, ALB, ASG, SNS 
    create_bucket(bucket_name)
    create_instance()

def update_infrastructure():
    # Code to update resources (e.g., scaling policies, instance upgrades)
    def update_scaling_policy(auto_scaling_group_name, scaling_policy_name, scaling_adjustment, cooldown):
        """
        Updates the scaling policies based on the new parameters.
        """
        response = autoscaling.put_scaling_policy(
            AutoScalingGroupName=auto_scaling_group_name,
            PolicyName=scaling_policy_name,
            ScalingAdjustment=scaling_adjustment,
            AdjustmentType='ChangeInCapacity',
            Cooldown=cooldown
        )
        print(f"Scaling policy {scaling_policy_name} updated with scaling adjustment {scaling_adjustment} and cooldown {cooldown} seconds.")
        return response

    def update_instance_type(asg_name, new_instance_type):
        """
        Updates the EC2 instance type in the Auto Scaling Group.
        """
        # Get the Launch Configuration name
        response = autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=[asg_name]
        )
        launch_config_name = response['AutoScalingGroups'][0]['LaunchConfigurationName']
    
        # Get the launch configuration details
        launch_config_response = autoscaling.describe_launch_configurations(
            LaunchConfigurationNames=[launch_config_name]
        )
        launch_config = launch_config_response['LaunchConfigurations'][0]
    
        # Modify the instance type in the launch configuration
        new_config = autoscaling.create_launch_configuration(
            LaunchConfigurationName=f"{launch_config_name}-updated",
            ImageId=launch_config['ImageId'],
            InstanceType=new_instance_type,
            KeyName=launch_config['KeyName'],
            SecurityGroups=launch_config['SecurityGroups'],
            UserData=launch_config['UserData']
        )
    
        print(f"Launch Configuration {launch_config_name} updated with new instance type {new_instance_type}.")
    
        # Update Auto Scaling Group with the new launch configuration
        response = autoscaling.update_auto_scaling_group(
            AutoScalingGroupName=AutoScalingGroupName,
            LaunchConfigurationName=f"{launch_config_name}-updated"
        )
    
        print(f"Auto Scaling Group {asg_name} updated to use the new launch configuration with instance type {new_instance_type}.")
        return response

    def update_resources():
        """
        Function to update scaling policies and instance types for the resources.
        """
        # Updating scaling policies
        update_scaling_policy(
            auto_scaling_group_name=AutoScalingGroupName,
            scaling_policy_name='scale-up-policy',
            scaling_adjustment=2,  # Increase by 2 instances instead of 1
            cooldown=600  # Increase cooldown time to 10 minutes
        )
    
        # Upgrading EC2 instance type in the Auto Scaling Group
        update_instance_type(
            asg_name=AutoScalingGroupName,
            new_instance_type='t2.nano'  # New instance type
        )

    # Call the function to update resources
    update_resources()


def teardown_infrastructure():
    # Delete all resources (EC2, ALB, ASG, SNS, S3, etc.)
    ec2.instances.filter(InstanceIds=[instance.id]).terminate()
    s3.delete_bucket(Bucket=bucket_name)
    elb.delete_load_balancer(LoadBalancerArn=alb_arn)
    asg.delete_auto_scaling_group(AutoScalingGroupName='sk-auto-scaling-group', ForceDelete=True)
    sns.delete_topic(TopicArn=sk-Health-Issues-Alert['TopicArn'])
    sns.delete_topic(TopicArn=sk-Scaling-Event-Alert['TopicArn'])
    sns.delete_topic(TopicArn=sk-High-Traffic-Alert['TopicArn'])

# To deploy
deploy_infrastructure()

# To update (call this function as needed)
update_infrastructure()

# To teardown
teardown_infrastructure()