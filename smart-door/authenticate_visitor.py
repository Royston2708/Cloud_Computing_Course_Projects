import json
import re
import boto3
import datetime
import string
import calendar
import random

def lambda_handler(event, context):
    # TODO implement
    # Retrieve body of response
    text = event["body"]
    print(text)


    # Extract values from response
    match = re.search("(?:name=)([^0-9]+)(?:\+)([^0-9]+)(?:&)(?:phone_num=)([0-9]+)(?:&)(?:faceID=)([0-9a-zA-Z-]+)", text)
    first_name = match.group(1)
    second_name = match.group(2)
    phone_num = match.group(3)
    final_phone_num = "+1{}".format(phone_num)
    faceID = match.group(4)
    print(first_name,second_name, final_phone_num)
    name = first_name + " " + second_name

    # Get image file name from temp photos
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('temp-photos')
    info = table.get_item(Key={'faceID': faceID,})
    img_filename = info["Item"]["lastImage"]

    # Create final item to input to Dynamo
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    newPhotoEntry = {
        "objectKey": img_filename,
        "bucket": "smart-door-bkt1",
        "timestamp": timestamp
    }
    photos = []
    photos.append(newPhotoEntry)
    item = {"name":name, "phoneNumber":final_phone_num, "faceID":faceID, "photos":photos}

    # Input final Item to Visitors
    finalTable = dynamodb.Table('visitors')
    finalTable.put_item(Item=item)

    # Create OTP for New Visitor
    letters_and_digits = string.ascii_letters + string.digits
    otp = ''.join((random.choice(letters_and_digits) for i in range(8)))

    # sending message with otp to number
    finalMessage = """Here is your OTP: {}. \nPlease enter passcode at http://passcode-auth-site.s3-website-us-east-1.amazonaws.com/""".format(otp)
    sns = boto3.client('sns')

    # Send a SMS message to the specified phone number
    messageSent = sns.publish(
          PhoneNumber= final_phone_num,
          Message= finalMessage,
          MessageAttributes = {
              'AWS.SNS.SMS.SMSType': {
                  'DataType': 'String',
                  'StringValue': 'Transactional'
              }

          }
    )

    # getting timestamp for 5 min in future
    future = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    entryTime = calendar.timegm(future.timetuple())

    # inserting passcode into table
    otp_table = dynamodb.Table('smart-door-passcodes')
    entry = {'passcode': otp, 'expTime': entryTime}
    response = otp_table.put_item(Item = entry)

    return {
        'statusCode': 200,
        'body': 'OTP has been sent to visitor!'
    }
