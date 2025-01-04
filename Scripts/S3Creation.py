import boto3

# Initialize S3 client
s3 = boto3.client('s3')

# Create the S3 bucket
bucket_name = 'sk-web-app-static-files-bucket'
s3.create_bucket(Bucket=bucket_name)

# Upload static files to S3
s3.upload_file('./HeroViredRepositories/templates/calculator.html', bucket_name, 'calculator.html')

