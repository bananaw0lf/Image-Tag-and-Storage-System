import boto3
import numpy as np
import cv2
import json
from io import BytesIO
import os
import time
import uuid
#Client object for interacting with Amazon S3
s3_obj_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')
table_name = 'detect_obj_db'
confthres = 0.3
nmsthres = 0.1
#Read image from s3
def read_image_from_s3(bucket_name,object_key):
    response = s3_obj_client.get_object(Bucket=bucket_name, Key=object_key)
    image_data = response['Body'].read()
    image_np = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(image_np,cv2.IMREAD_COLOR)
    return image
def store_tags_in_dynamodb(image_name,tags,thumbnail_s3_uri,raw_image_uri):
    try:
        response = dynamodb_client.put_item(
            TableName=table_name,
            Item={
                'image_name': {'S': image_name},
                'thumbnail_image_url': {'S': thumbnail_s3_uri},
                'raw_image_url': {'S': raw_image_uri},
                'tags': {'SS': tags}
            }
        )
        return response
    except Exception as e:
        print(f"Error storing tags in DynamoDB: {e}")
        return None
def do_prediction(image, net, LABELS):
    (H, W) = image.shape[:2]
    ln = net.getLayerNames()
    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layerOutputs = net.forward(ln)
    end = time.time()

    boxes = []
    confidences = []
    classIDs = []

    for output in layerOutputs:
        for detection in output:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            if confidence > confthres:
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)

    idxs = cv2.dnn.NMSBoxes(boxes, confidences, confthres, nmsthres)

    results = []
    if len(idxs) > 0:
        for i in idxs.flatten():
            results.append({
                "label": LABELS[classIDs[i]],
                "confidence": confidences[i],
                "box": {
                    "x": boxes[i][0],
                    "y": boxes[i][1],
                    "width": boxes[i][2],
                    "height": boxes[i][3]
                }
            })
    return results
def lambda_handler(event, context):
    try:
        unique_id = str(uuid.uuid4())
        # Extract bucket name and object key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        raw_image_bucket = "rawimagess3p"
        raw_image_key = "uploads/"
        image_name = key.split('/')[-1]
        raw_image_object_key = raw_image_key + image_name
        thumbnail_s3_uri = get_s3_uri(bucket, key)
        raw_image_uri = get_s3_uri(raw_image_bucket,raw_image_object_key)
        # Read the image that triggered the event
        image = read_image_from_s3(bucket, key)
        # Define paths to YOLO model files (assuming they're included in your Lambda layer or deployment package)
        yolo_path = '/opt/yolo_tiny_configs'
        labelsPath = os.path.join(yolo_path, "coco.names")
        cfgpath = os.path.join(yolo_path, "yolov3-tiny.cfg")
        wpath = os.path.join(yolo_path, "yolov3-tiny.weights")
        Lables = get_labels(labelsPath)
        CFG = get_config(cfgpath)
        Weights = get_weights(wpath)
        nets = load_model(CFG, Weights)
        # Perform prediction
        predictions = do_prediction(image, nets, Lables)
        tags = list(set([pred['label'] for pred in predictions]))
        store_tags_in_dynamodb(image_name,tags,thumbnail_s3_uri,raw_image_uri)
        return {
            'statusCode': 200,
            'body': json.dumps("recorded in database")
        }

    except Exception as e:
        print(f"Exception: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }

def get_labels(labels_path):
    LABELS = open(labels_path).read().strip().split("\n")
    return LABELS

def get_weights(weights_path):
    return weights_path

def get_config(config_path):
    return config_path

def load_model(configpath, weightspath):
    net = cv2.dnn.readNetFromDarknet(configpath, weightspath)
    return net
def get_s3_uri(bucket, key):
    return f"s3://{bucket}/{key}"