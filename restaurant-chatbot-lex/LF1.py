import json
import boto3
import random


def lambda_handler(event, context):
    # TODO implement

    intent_name = event.get("currentIntent").get("name")


    if intent_name == "greetingIntent":
        response = "Hey, how can I help you today?"
        return {
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Fulfilled",
                "message": {
                    "contentType": "PlainText",
                    "content": response
                }
            }
        }

    if intent_name == "thankYouIntent":

        response = "It was a pleasure assisting you. Have a great time!"
        return {
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Fulfilled",
                "message": {
                    "contentType": "PlainText",
                    "content": response
                }
            }
        }

    if intent_name == "diningIntent":

        city_name = event.get("currentIntent").get("slots").get("Location")
        cuisine = event.get("currentIntent").get("slots").get("Cuisine")
        print("The Cuisine is {}".format(cuisine))
        time = event.get("currentIntent").get("slots").get("Time")
        people = event.get("currentIntent").get("slots").get("People")
        number = event.get("currentIntent").get("slots").get("Number")


        if city_name is None:
            return {
                "dialogAction": {
                    "type": "ElicitSlot",
                    "message": {
                      "contentType": "PlainText",
                      "content": "What city are you in ?"
                    },
                "intentName": "diningIntent",
                "slots": {
                    "Location": city_name,
                    "Cuisine": cuisine,
                    "People": people,
                    "Time":time,
                    "Number":number
                },
                "slotToElicit" : "Location"
                }
            }

        elif people is None:
            return {
                "dialogAction": {
                    "type": "ElicitSlot",
                    "message": {
                      "contentType": "PlainText",
                      "content": "How many people are in your party?"
                    },
                "intentName": "diningIntent",
                "slots": {
                    "Location": city_name,
                    "Cuisine": cuisine,
                    "People": people,
                    "Time":time,
                    "Number":number
                },
                "slotToElicit" : "People"
                }
            }

        elif time is None:
            return {
                "dialogAction": {
                    "type": "ElicitSlot",
                    "message": {
                      "contentType": "PlainText",
                      "content": "What time would you like to be seated ? (Enter military time as HHMM )"
                    },
                "intentName": "diningIntent",
                "slots": {
                    "Location": city_name,
                    "Cuisine": cuisine,
                    "People": people,
                    "Time":time,
                    "Number":number
                },
                "slotToElicit" : "Time"
                }
            }

        elif cuisine is None:
            return {
                "dialogAction": {
                    "type": "ElicitSlot",
                    "message": {
                      "contentType": "PlainText",
                      "content": "What type of food/Cuisine are you looking for?"
                    },
                "intentName": "diningIntent",
                "slots": {
                    "Location": city_name,
                    "Cuisine": cuisine,
                    "People": people,
                    "Time":time,
                    "Number":number
                },
                "slotToElicit" : "Cuisine"
                }
            }

        elif number is None:
            return {
                "dialogAction": {
                    "type": "ElicitSlot",
                    "message": {
                      "contentType": "PlainText",
                      "content": "What is your contact number? (Please enter 10 digit US mobile number)"
                    },
                "intentName": "diningIntent",
                "slots": {
                    "Location": city_name,
                    "Cuisine": cuisine,
                    "People": people,
                    "Time":time,
                    "Number":number
                },
                "slotToElicit" : "Number"
                }
            }

        else:
            sqs_client = boto3.client('sqs')
            queue_url = "https://sqs.us-west-2.amazonaws.com/884631752477/diningQueue"

            response = sqs_client.send_message(
                QueueUrl=queue_url,
                DelaySeconds=10,
                MessageAttributes={
                    'Location': {
                        'DataType': 'String',
                        'StringValue': city_name
                    },
                    'Cuisine': {
                        'DataType': 'String',
                        'StringValue': cuisine
                    },
                    'People': {
                        'DataType': 'Number',
                        'StringValue': "{}".format(people)
                    },
                    'Time': {
                        'DataType': 'String',
                        'StringValue': time
                    },
                    'Number': {
                        'DataType': 'Number',
                        'StringValue': "{}".format(number)
                    }
                },
                MessageBody=(
                    'Values filled in by the customer.'
                )
            )

            front_response = "We have received your request. You will receive a text shortly"
            return {
                "dialogAction": {
                    "type": "Close",
                    "fulfillmentState": "Fulfilled",
                    "message": {
                        "contentType": "PlainText",
                        "content": front_response
                    }
                }
            }
