import json
import boto3
import cv2
import numpy as np
import os

s3_client = boto3.client('s3')


def lambda_handler(event, context):
    try:
        # Get the bucket name and object key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        # Download the image from S3
        download_path = f"/tmp/{os.path.basename(key)}"
        s3_client.download_file(bucket, key, download_path)
        try:
            # Read the image using OpenCV
            image = cv2.imread(download_path)
        except:
            return {
                'statusCode': 500,
                'body': json.dumps("Image Error")
            }
        try:
            # Create a thumbnail
            thumbnail = create_thumbnail(image, (128, 128))
        except:
            return {
                'statusCode': 500,
                'body': json.dumps('thumbnail creation failed')
            }

        # Save the thumbnail to a temporary path
        thumbnail_path = f"/tmp/thumbnail-{os.path.basename(key)}"
        cv2.imwrite(thumbnail_path, thumbnail)

        # Upload the thumbnail to the new S3 bucket
        thumbnail_bucket = 'imagethumbnails'
        thumbnail_key = f"thumbnails/{os.path.basename(key)}"
        try:
            s3_client.upload_file(thumbnail_path, thumbnail_bucket, thumbnail_key)
        except:
            return {
                'statusCode': 200,
                'body': json.dumps('Error writting file to S3')
            }

        return {
            'statusCode': 200,
            'body': json.dumps('Thumbnail created successfully')
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps('Error creating thumbnail')
        }


def create_thumbnail(image, size):
    # Resize the image while maintaining aspect ratio
    h, w = image.shape[:2]
    aspect_ratio = w / h
    if w > h:
        new_w = size[0]
        new_h = int(new_w / aspect_ratio)
    else:
        new_h = size[1]
        new_w = int(new_h * aspect_ratio)

    thumbnail = cv2.resize(image, (new_w, new_h))

    # Center the thumbnail in a blank canvas of the desired size
    canvas = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    canvas[(size[1] - new_h) // 2:(size[1] - new_h) // 2 + new_h,
    (size[0] - new_w) // 2:(size[0] - new_w) // 2 + new_w] = thumbnail

    return canvas
