import json
import boto3
from urllib.parse import unquote

s3_client = boto3.client('s3')
dynamo_db = boto3.resource('dynamodb')
table = dynamo_db.Table('detect_obj_db')


def lambda_handler(event, context):
    http_method = event['httpMethod']

    if http_method == 'GET':
        return list_images(event, context)
    elif http_method == 'POST':
        return delete_images(event, context)
    else:
        return build_response(405, {'message': f'Method {http_method} not allowed'})


def list_images(event, context):
    try:
        # Scan DynamoDB table to list all images
        response = table.scan()
        items = response.get('Items', [])

        # Extract URLs for each item
        image_urls = [item['thumbnail_image_url'] for item in items]
        return build_response(200, {'images': image_urls})

    except Exception as e:
        return build_response(500, {'message': 'Internal server error', 'error': str(e)})


def delete_images(event, context):
    try:
        body = json.loads(event['body'])
        image_urls = body.get('image_urls', [])

        if not image_urls:
            return build_response(400, {'message': 'No image URLs provided'})

        deleted_images = []
        failed_images = []

        for image_url in image_urls:
            try:
                # Extract image name from URL
                image_name = unquote(image_url.split('/')[-1])

                # Delete from S3
                s3_thumbnail_key = f'thumbnails/{image_name}'
                s3_raw_key = f'uploads/{image_name}'

                s3_client.delete_object(Bucket='imagethumbnails', Key=s3_thumbnail_key)
                s3_client.delete_object(Bucket='rawimagess3p', Key=s3_raw_key)

                # Delete from DynamoDB
                response = table.delete_item(
                    Key={'image_name': image_name}
                )

                # Record successfully deleted image
                deleted_images.append(image_url)

            except Exception as e:
                print(f"Failed to delete image {image_url}: {e}")
                failed_images.append(image_url)

        return build_response(200, {'deleted_images': deleted_images, 'failed_images': failed_images})

    except json.JSONDecodeError:
        return build_response(400, {'message': 'Invalid JSON format'})

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
