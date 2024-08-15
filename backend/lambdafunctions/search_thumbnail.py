import json
import boto3

dynamo = boto3.resource('dynamodb')
table = dynamo.Table('detect_obj_db')

def thumbnail_search(event, context):
    http_method = event['httpMethod']
    if http_method == 'POST':
        try:
            body = json.loads(event['body'])
            thumbnail_url = body.get('url')
            if not thumbnail_url:
                return build_response(400, {'message': 'thumbnail_url is required in the request body'})
            image_name = thumbnail_url.split('/')[-1]
            response = table.get_item(Key={'image_name': image_name})
            if 'Item' in response:
                thumbnail_url = response['Item'].get('thumbnail_image_url')
                return build_response(200, {'thumbnail_url': thumbnail_url})
            else:
                return build_response(404, {'message': 'Item not found'})
        except json.JSONDecodeError:
            return build_response(400, {'message': 'Invalid JSON format'})
        except Exception as e:
            return build_response(500, {'message': 'Internal server error', 'error': str(e)})
    else:
        return build_response(405, {'message': f'Method {http_method} not allowed'})

def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'body': json.dumps(body),
        'headers': {
            'Content-Type': 'application/json'
        }
    }
