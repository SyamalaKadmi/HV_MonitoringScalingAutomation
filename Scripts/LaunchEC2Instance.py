import boto3;

ec2 = boto3.resource('ec2')

#Launch EC2 instance
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