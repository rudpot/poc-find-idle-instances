import json
import boto3
import datetime

ec2_client = boto3.client("ec2")
cw_client = boto3.client("cloudwatch")

KEY_NAME="AutoStop"
DEFAULT_THRESHOLD=10

def get_running_instances():
    instances = []
    try:
        result = ec2_client.describe_instances(
            Filters = [
                {
                    'Name': 'instance-state-name',
                    'Values': [ 'running' ]
                },
                {
                    "Name": "tag-key",
                    "Values": [ "AutoStop" ]
                }
            ]
        )
        for ii in result.get('Reservations',[{}]):
            for jj in ii.get('Instances',[{}]):
                threshold=DEFAULT_THRESHOLD
                for kk in jj.get("Tags",[{}]):
                    if (kk.get("Key","") == KEY_NAME) and (kk.get("Value","") != ""):
                        threshold = float(kk.get("Value","-1"))
                instances.append(
                    { 
                        "id": jj.get('InstanceId',None),
                        "threshold": threshold
                    }
                )
        return instances
    except Exception as e:
        print(repr(e))
        return []


def get_cw_data_for_instance(instance_id):
    try:
        data = cw_client.get_metric_data(
            MetricDataQueries=[
                {
                    "Id": "cpu",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/EC2",
                            "MetricName": "CPUUtilization",
                            "Dimensions": [
                                {
                                    "Name": "InstanceId",
                                    "Value": instance_id
                                }
                            ],
                        },
                        "Period": 60,
                        "Unit": "Percent",
                        "Stat": "Average"
                    },
                    "ReturnData": True,
                }
            ],
            StartTime = datetime.datetime.now()-datetime.timedelta(hours=8),
            EndTime = datetime.datetime.now()
        )
        # print(instance_id)
        # print(data)
        cpu_sum = 0
        cpu_cnt = 0
        for ii in data.get("MetricDataResults",[]):            
            cpu_sum += sum(ii.get("Values",[]))
            cpu_cnt += len(ii.get("Values",[]))
        cpu_avg = cpu_sum/cpu_cnt
        # print("cpu avg %f from %f/%f" %(cpu_avg,cpu_sum,cpu_cnt))
        return cpu_avg

    except Exception as e:
        print(repr(e))



def lambda_handler(event, context):

    running_instances = get_running_instances()
    print(running_instances)

    killable_instances = []
    for instance_info in running_instances:
        instance_id = instance_info["id"]
        instance_threshold = instance_info["threshold"]
        cpu_avg = get_cw_data_for_instance(instance_id)
        if cpu_avg < instance_threshold:
            killable_instances.append(instance_id)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            "data": killable_instances
        }),
    }

print(lambda_handler(None,None))