import boto3

def create_table():
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.create_table(
        TableName='yelp-restaurants',
        KeySchema = [
            {
                'AttributeName':'restaurantID',
                'KeyType':'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName':'restaurantID',
                'AttributeType':'S'
            }
        ]
    )

create_table()
