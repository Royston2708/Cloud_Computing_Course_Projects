import json
import boto3

def lambda_handler(event, context):

    input_text = (event.get("messages")[0].get("unstructured").get("text"))

    client = boto3.client('lex-runtime')
    response = client.post_text(
        botName='restaurantChatbox',
        botAlias='rsChat',
        userId= "id",
        inputText= input_text)
    print(response)
    return {
        'headers': {
            'Access-Control-Allow-Origin': '*'

        },
        'messages': [ {'type': "unstructured", 'unstructured': {'text': response.get("message")}  } ]

    }
