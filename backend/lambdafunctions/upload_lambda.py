import json
import boto3
import base64
import uuid
from botocore.exceptions import ClientError

s3_client_upload = boto3.client('s3')


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        # Access the Image Data
        image_data = body['image']
        # Decode the base 64 image
        image_content = base64.b64decode(image_data)
        # Have file name or generate unique id for each image file and use it as object key
        create_object_key = body.get('file_name', str(uuid.uuid4()) + '.jpg')
        bucket_name = 'rawimagess3p'
        object_key = f'uploads/{create_object_key}'
        # Upload image to S3
        # Check if bucket already exists or create bucket
        try:
            s3_client_upload.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                try:
                    s3_client_upload.create_bucket(Bucket=bucket_name)
                except Exception as e:
                    return {
                        'statusCode': 200,
                        'body': json.dumps({'message': '!!Something went wrong'})
                    }
        s3_client_upload.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=image_content,
            ContentType='image/jpeg'
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'File Uploaded Successfully to S3', 'file_name': create_object_key})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

