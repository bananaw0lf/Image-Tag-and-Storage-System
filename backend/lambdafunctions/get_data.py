import json
import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    try:
        # Log the incoming event
        print("Received event:", json.dumps(event))

        # Initializing DynamoDB resource
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('detect_obj_db')

        # Scan DynamoDB table to retrieve all items
        response = table.scan()

        # Extract items from response and create a list of dictionaries with 'thumbnail_image_url' and 'tags' only
        items = [{'thumbnail_image_url': item['thumbnail_image_url'], 'tags': list(item.get('tags', []))}
                 for item in response.get('Items', [])]

        # Return response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Retrieved thumbnail URLs and tags successfully',
                'items': items
            })
        }

    except ClientError as e:
        print(f"Error retrieving items: {e.response['Error']['Message']}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error retrieving items: {e.response["Error"]["Message"]}')
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
