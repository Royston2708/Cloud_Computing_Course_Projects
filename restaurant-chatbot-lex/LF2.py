import json
import boto3
import random
from elasticsearch import Elasticsearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth

def lambda_handler(event, context):

    sqs = boto3.client('sqs')
    sns = boto3.client('sns')
    dynamodb = boto3.resource('dynamodb')
    queue_url = "https://sqs.us-west-2.amazonaws.com/884631752477/diningQueue"

    access_key = "****************"
    secret_key = "*******************************"
    host = "search-test-es-55h2alnoth4r7l4hkldymkn7m4.us-west-2.es.amazonaws.com"
    region = 'us-west-2'
    service = "es"
    awsauth = AWSRequestsAuth(aws_access_key = access_key, aws_secret_access_key = secret_key,
        aws_region = region, aws_service = service, aws_host = host)

    es = Elasticsearch(hosts = [{'host': host, 'port': 443}],
                       http_auth = awsauth, use_ssl = True,
                       verify_certs = True, connection_class = RequestsHttpConnection)

    # polling messaging from sqs
    response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1,
    MessageAttributeNames=[
        'All'
    ],
    VisibilityTimeout=0,
    WaitTimeSeconds=0)

    try:
        # sending desired cuisine to query elastic
        message = response['Messages'][0]
        cuisine = message['MessageAttributes'].get('Cuisine').get('StringValue')
        number = message['MessageAttributes'].get('Number').get('StringValue')
        modifiedNumber = "+1{}".format(number)

        # elastic fetches the restaurant id for cuisine type

        res = es.search(index="restaurants", body={"query": {"match": {"cuisine": cuisine}}})
        candidates = []
        for entry in res['hits']['hits']:
          candidates.append(entry["_source"])
        ids = []
        for c in candidates:
          ids.append(c.get("id"))

        restaurant_suggestion = random.choice(ids)
        temp_id = restaurant_suggestion

        # query DynamoDb table to get more info
        table = dynamodb.Table('yelp-restaurants')
        info = table.get_item(
        Key={
            'id': temp_id,
            }
        )

        finRating = info["Item"]["rating"]
        finName = info["Item"]["name"]
        finRatingCount = info["Item"]["review_count"]
        finRating = info["Item"]["rating"]
        finAddress = info["Item"]["address1"]
        finZip = info["Item"]["zip_code"]

        # message to send to customer
        finalMessage = """I recommend going to: {}. It has {} reviews
        with an average {} rating. The address is: {}, {}. Your text was sent to:
        {}.
        """.format(finName, finRatingCount, finRating, finAddress, finZip, modifiedNumber)

        print(finalMessage)
        # Send a SMS message to the specified phone number
        messageSent = sns.publish(
            PhoneNumber= modifiedNumber,
            Message= finalMessage,
        )

        # Deleting the SQS Entry
        receipt_handle = message['ReceiptHandle']
        sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle)

        return {
            'statusCode': 200,
            'body': finalMessage
        }

    except:
        return {
            'statusCode': 200,
            'body': 'no message'
        }
