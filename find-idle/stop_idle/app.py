import json
import boto3

ec2_client = boto3.client("ec2")


# {
#   "Records": [
#     {
#       "EventSource": "aws:sns",
#       "EventVersion": "1.0",
#       "EventSubscriptionArn": "arn:aws:sns:us-east-1:{{{accountId}}}:ExampleTopic",
#       "Sns": {
#         "Type": "Notification",
#         "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
#         "TopicArn": "arn:aws:sns:us-east-1:123456789012:ExampleTopic",
#         "Subject": "example subject",
#         "Message": "example message",
#         "Timestamp": "1970-01-01T00:00:00.000Z",
#         "SignatureVersion": "1",
#         "Signature": "EXAMPLE",
#         "SigningCertUrl": "EXAMPLE",
#         "UnsubscribeUrl": "EXAMPLE",
#         "MessageAttributes": {
#           "Test": {
#             "Type": "String",
#             "Value": "TestString"
#           },
#           "TestBinary": {
#             "Type": "Binary",
#             "Value": "TestBinary"
#           }
#         }
#       }
#     }
#   ]
# }
def lambda_handler(event, context):

    try:
        instance_ids = []
        for record in event.get("Records",{}):
            if record.get("EventSource", "") == "aws:sns":
                ids = json.loads(record.get("Sns", {}).get("Message",[]))
                instance_ids += ids
        
        ec2_client.stop_instances(
            InstanceIds = instance_ids
        ) 
        
    except Exception as e:
        print(repr(e))
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Failed to stop instances",
                "data": repr(e)
            }),
        }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Successfully sent stop signal to instances",
            "data": instance_ids
        }),
    }

