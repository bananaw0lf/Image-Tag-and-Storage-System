import json
import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    try:
        # Log the incoming event
        print("Received event:", json.dumps(event))

        # Extracting the data from the event body
        body = event.get('body')
        if body:
            body = json.loads(body)
        else:
            # Assuming event contains the body directly if not found under 'body' key
            body = event

        urls = body.get('url', [])
        operation_type = body.get('type')
        tags = body.get('tags', [])

        if not urls or operation_type is None or not tags:
            return {
                'statusCode': 400,
                'body': json.dumps('Invalid input data')
            }

        # Initializing DynamoDB resource
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('detect_obj_db')
        # List to store updated items
        updated_items = []
        for url in urls:
            try:
                # Query DynamoDB to find the item by URL
                response = table.scan(
                    FilterExpression="thumbnail_image_url = :url",
                    ExpressionAttributeValues={":url": url}
                )
                items = response.get('Items', [])

                if not items:
                    print(f"No item found for URL: {url}")
                    return {
                        'statusCode': 500,
                        'body': json.dumps('no items to update')
                    }

                item = items[0]
                image_name = item['image_name']
                existing_tags = set(item.get('tags', []))

                if operation_type == 1:
                    # Add tags
                    updated_tags = existing_tags.union(tags)
                    update_expression = "ADD tags :tags"
                    expression_attribute_values = {':tags': updated_tags}
                elif operation_type == 0:
                    # Remove tags
                    updated_tags = existing_tags.difference(tags)
                    update_expression = "DELETE tags :tags"
                    expression_attribute_values = {':tags': set(tags)}  # Use set to ensure unique values
                else:
                    continue

                # Update the item in DynamoDB
                table.update_item(
                    Key={'image_name': image_name},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values
                )

                updated_item = {
                    'image_name': image_name,
                    'raw_image_url': item.get('raw_image_url'),
                    'thumbnail_image_url': item.get('thumbnail_image_url'),
                    'tags': list(updated_tags)  # Convert tags set to list for response
                }
                updated_items.append(updated_item)

            except ClientError as e:
                print(f"Error updating item: {e.response['Error']['Message']}")
                return {
                    'statusCode': 500,
                    'body': json.dumps(f'Error updating DynamoDB: {e.response["Error"]["Message"]}')
                }

        return {
            'statusCode': 200,
            'body': json.dumps('Tags updated successfully'),
            'updated_items': updated_items
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
