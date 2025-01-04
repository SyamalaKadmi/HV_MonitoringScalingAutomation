import boto3

# Initialize the Boto3 SNS client
sns_client = boto3.client('sns', region_name='us-east-1')  # Set your AWS region
lambda_client = boto3.client('lambda', region_name='us-east-1')  # For Lambda integration

# Define SNS Topic names
topics = {
    "sk-Health-Issues-Alert": "Health issues in your infrastructure",
    "sk-Scaling-Event-Alert": "Scaling events for your infrastructure",
    "sk-High-Traffic-Alert": "High traffic alert in your application"
}

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
    topic_arns = {'arn:aws:sns:us-east-1:975050024946:sk-Health-Issues-Alert', 'arn:aws:sns:us-east-1:975050024946:sk-High-Traffic-Alert', 'arn:aws:sns:us-east-1:975050024946:sk-Scaling-Event-Alert'}
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

if __name__ == '__main__':
    setup_notifications()
