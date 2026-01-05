#!/bin/bash

until curl -f http://localhost:4566/_localstack/health; do
  echo "Waiting for LocalStack..."
  sleep 2
done

echo "Creating SQS queues..."

# Create DLQ first
aws --endpoint-url=http://localhost:4566 sqs create-queue \
    --queue-name carbon-events-dlq \
    --region us-east-1

# Get DLQ ARN
DLQ_URL=$(aws --endpoint-url=http://localhost:4566 sqs get-queue-url \
    --queue-name carbon-events-dlq \
    --region us-east-1 \
    --query 'QueueUrl' \
    --output text)

DLQ_ARN="arn:aws:sqs:us-east-1:000000000000:carbon-events-dlq"

# Create Celery queue with DLQ redrive policy
aws --endpoint-url=http://localhost:4566 sqs create-queue \
    --queue-name celery \
    --region us-east-1 \
    --attributes "{
        \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"${DLQ_ARN}\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"
    }"

echo "SQS queues created with DLQ configuration!"