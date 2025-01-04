import boto3
import json

# Initialize the boto3 client for SNS and Lambda
sns_client = boto3.client('sns')
lambda_client = boto3.client('lambda')

# Define the SNS topics for different alerts
sns_topics = {
    "sk-Health-Issues-Alert",
    "sk-Scaling-Event-Alert",
    "sk-High-Traffic-Alert"
}

# Lambda function for processing notifications (example Lambda ARN)
lambda_function_arn = 'arn:aws:lambda:us-east-1:975050024946:function:sk_applifecycle_automation'

# Function to invoke Lambda for processing notifications
def invoke_lambda(topic_name, message):
    payload = {
        'topic': topic_name,
        'message': message
    }
    response = lambda_client.invoke(
        FunctionName=lambda_function_arn,
        InvocationType='Event',  # Asynchronous invocation
        Payload=json.dumps(payload)
    )
    print(f"Lambda invocation response for {topic_name}: {response}")

#Simulating event that triggers a notification
def trigger_alert(topic_name, topic_arn, message):
    sns_client.publish(
        TopicArn=topic_arn,
        Message=message,
        Subject=f"Alert: {topic_name.capitalize()} Notification"
    )
    print(f"Alert triggered for {topic_name}: {message}")
    invoke_lambda(topic_name, message)

#triggering an alert (scaling event)
trigger_alert('sk-Scaling-Event-Alert', 'arn:aws:sns:us-east-1:975050024946:sk-Scaling-Event-Alert', 'Auto Scaling has triggered due to high load.')

#triggering an alert (high traffic)
trigger_alert('sk-High-Traffic-Alert', 'arn:aws:sns:us-east-1:975050024946:sk-High-Traffic-Alert', 'Website traffic has exceeded the defined threshold.')

#triggering an alert (health issue)
trigger_alert('sk-Health-Issues-Alert', 'arn:aws:sns:us-east-1:975050024946:sk-Health-Issues-Alert', 'A server in the Auto Scaling Group is unhealthy.')
