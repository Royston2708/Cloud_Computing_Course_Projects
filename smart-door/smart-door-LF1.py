import json
import base64
import random
import string
import boto3
import datetime
import calendar
import cv2

def get_byte_stream_from_kinesis():
	kinesis_client = boto3.client('kinesisvideo', region_name = 'us-east-1')
	response = kinesis_client.get_data_endpoint(StreamARN = 'arn:aws:kinesisvideo:us-east-1:671455739102:stream/kvs-x/1606190631289', APIName = 'GET_MEDIA')
	video_client = boto3.client('kinesis-video-media', endpoint_url = response['DataEndpoint'], region_name = 'us-east-1')
	response = video_client.get_media(StreamARN= 'arn:aws:kinesisvideo:us-east-1:671455739102:stream/kvs-x/1606190631289', StartSelector = {'StartSelectorType':'NOW'})
	payload = response['Payload']
	return payload


def lambda_handler(event, context):

    data_raw = event['Records'][0]['kinesis']['data']
    data_str = base64.b64decode(data_raw).decode('ASCII')
    data = json.loads(data_str)

    # get image and upload it to s3 bucket
    payload = get_byte_stream_from_kinesis()
    byte_iter = payload.iter_chunks()
    with open("/tmp/myfile.txt", "ab+") as byte_file:
    	success = False
    	while not success:
    		output = next(byte_iter, None)
    		if output == None:
    		    break

    		byte_file.write(output)

    		# Capture Image from Byte File
    		vidcap = cv2.VideoCapture("/tmp/myfile.txt")
    		success, image = vidcap.read()

    		if success:
    		    fileLetters = string.ascii_letters + string.digits
    		    randomFileName = ''.join((random.choice(fileLetters) for i in range(16)))
    		    filename = "/tmp/{}.png".format(randomFileName)
    		    cv2.imwrite(filename, image)
    		    pngFileName = "{}.png".format(randomFileName)

    		    # add to spammer bucket
    		    s3 = boto3.client('s3')
    		    s3.upload_file(filename, "spammer-bucket", pngFileName)

    		    rekogClient=boto3.client('rekognition')
    		    rekogResponse=rekogClient.search_faces_by_image(
    		        CollectionId='new-smart-door-faces',
    		        Image={'S3Object':{'Bucket':'spammer-bucket', 'Name': pngFileName}},
    		        FaceMatchThreshold=85.5,
    		        MaxFaces=1
    		    )
    		    faceMatches=rekogResponse['FaceMatches']

    		    # add to collection and get face id
    		    if len(faceMatches) == 0:
    		        addedResponse=rekogClient.index_faces(
    		            CollectionId="new-smart-door-faces",
    		            Image={'S3Object':{'Bucket':'spammer-bucket', 'Name': pngFileName}},
    		            ExternalImageId=randomFileName,
    		            MaxFaces=1,
    		            QualityFilter="AUTO",
    		            DetectionAttributes=['ALL']
    		        )
    		        for faceRecord in addedResponse['FaceRecords']:
    		            imageFaceID = faceRecord['Face']['FaceId']

    		    # retrieve face id without adding to collection
    		    else:
    		        for match in faceMatches:
    		            imageFaceID = match['Face']['FaceId']

    		    dynamodb = boto3.resource('dynamodb')
    		    temp_table = dynamodb.Table('temp-photos')
    		    info = temp_table.get_item(Key={'faceID': imageFaceID,})
    		    try:
    		        lastTimestamp = info["Item"]["timestamp"]
    		        timeBound = datetime.datetime.utcnow()
    		        currentTime = calendar.timegm(timeBound.timetuple())
    		        # spam entry so we return
    		        if (lastTimestamp > currentTime):
    		            return "spam entry not processed"
    		    except KeyError:
    		        print("")

    		    expirationTimestamp = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    		    processedExpiration = calendar.timegm(expirationTimestamp.timetuple())
    		    newTempEntry = {'faceID': imageFaceID, 'timestamp':processedExpiration, 'lastImage': pngFileName}
    		    responseTemp = temp_table.put_item(Item = newTempEntry)

    		    # Uploading image to S3 for legit entries
    		    s3.upload_file(filename, "smart-door-bkt1", pngFileName)
    		    print('filename: ', pngFileName)

    sns = boto3.client('sns')
    # check for known face
    if len(data['FaceSearchResponse'][0]['MatchedFaces']) > 0:
        faceID = data["FaceSearchResponse"][0]["MatchedFaces"][0]["Face"]["FaceId"]

        #generating one time password
        letters_and_digits = string.ascii_letters + string.digits
        otp = ''.join((random.choice(letters_and_digits) for i in range(8)))

        # getting DynamoDB item
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('visitors')

        visitor_info = table.get_item(Key={'faceID': faceID,})

        # can only get values if faceId exists
        try:
            # Getting Phone Number
            phoneNumber = visitor_info["Item"]["phoneNumber"]

            # Creating Item to be inputted back to the
            timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            photos = visitor_info["Item"]["photos"]
            newPhotoEntry = {
                "objectKey": "{}.png".format(randomFileName),
                "bucket": "smart-door-bkt1",
                "timestamp": timestamp

            }

            photos.append(newPhotoEntry)
            entryName = visitor_info["Item"]["name"]
            newTableEntry = {
                "faceID": faceID,
                "name": entryName,
                "phoneNumber": phoneNumber,
                "photos":photos

            }

            table.put_item(Item=newTableEntry)

            #sending message with otp to number
            finalMessage = """Here is your OTP: {}.Please enter passcode at http://passcode-auth-site.s3-website-us-east-1.amazonaws.com/""".format(otp)

            # Send a SMS message to the specified phone number
            messageSent = sns.publish(
                  PhoneNumber= phoneNumber,
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

            # return since succesful
            return "sent otp to known visitor"

        # faceID is not a known face
        except KeyError:
            print("not a known visitor")


    # unknown face logic
    approval_message = "Please approve visitor here: http://smart-door-visitor-page.s3-website-us-east-1.amazonaws.com/?faceID={}".format(imageFaceID)

    # Send a SMS message to the owner
    messageSent = sns.publish(
          PhoneNumber= '+16464314945',
          Message= approval_message,
          MessageAttributes = {
              'AWS.SNS.SMS.SMSType': {
                  'DataType': 'String',
                  'StringValue': 'Transactional'
              }
          }
    )

    return "sent message to owner to approve visitor"
    
