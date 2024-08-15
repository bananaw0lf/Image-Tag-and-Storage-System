import json
import boto3
from botocore.exceptions import ClientError

dynamo = boto3.resource('dynamodb')
table = dynamo.Table('todos1')  # Replace 'todos1' with your DynamoDB table name


def lambda_handler(event, context):
    try:
        # Check if running in the AWS Lambda console or API Gateway
        if 'httpMethod' in event:
            method = event['httpMethod']
        else:
            # Assuming POST for direct Lambda console testing
            method = 'POST'

        if method == 'POST':
            body = json.loads(event['body'])
            tags = body.get('tags')
            if not tags:
                return build_response(400, {'message': 'Tags are required in the request body'})

            # Query DynamoDB for matching images based on tags
            try:
                response = table.scan(
                    FilterExpression='contains(tags, :tag)',
                    ExpressionAttributeValues={':tag': tags[0]}
                )
                matching_image_urls = [item['thumbnail_image_url'] for item in response.get('Items', [])]
            except ClientError as e:
                return build_response(500, {'message': 'Error querying DynamoDB', 'error': str(e)})

            return build_response(200, {'links': matching_image_urls})
        else:
            return build_response(405, {'message': f'Method {method} not allowed'})
    except Exception as e:
        return build_response(500, {'message': 'Internal server error', 'error': str(e)})


def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'body': json.dumps(body),
        'headers': {
            'Content-Type': 'application/json'
        }
    }
