import json
import re
import datetime
import calendar
import boto3

def lambda_handler(event, context):
    text = event["body"]
    match = re.search("(?:otp=)([0-9a-zA-z]+)", text)
    otp = match.group(1)

    # Get passcode from passcode table
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('smart-door-passcodes')
    info = table.get_item(Key={'passcode': otp,})
    try:
        expireTime = info["Item"]["expTime"]
        currentTime = datetime.datetime.utcnow()
        currentProcessedTime = calendar.timegm(currentTime.timetuple())
        # valid passcode so delete passcode after entry
        if expireTime > currentProcessedTime:
            table.delete_item(Key={'passcode' : otp,})
            return {
                'statusCode': 200,
                'body': json.dumps('Passcode Valid! Welcome in')
            }
        # expired passcode
        else:
            return {
                'statusCode': 200,
                'body': json.dumps('Passcode invalid. Access Denied!')
            }
    except KeyError:
        return {
                'statusCode': 200,
                'body': json.dumps('Passcode invalid. Access Denied!')
            }
