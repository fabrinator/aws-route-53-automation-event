import json, boto3
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def get_hosted_zone_id(zone_name):
    client = get_route53_client()

    # List hosted zones by name
    response = client.list_hosted_zones_by_name(DNSName=zone_name, MaxItems="1")

    # Check if the response contains the hosted zone
    hosted_zones = response.get('HostedZones', [])
    if hosted_zones:
        for zone in hosted_zones:
            if zone['Name'] == zone_name + '.':
                return zone['Id'].split('/')[-1]  # Extract the zone ID from the full ARN
    return None

def get_route53_client():
    return boto3.client('route53')

def change_resource_record(record_name, record_type, record_value, zone_id, action):
    client = get_route53_client()
    try:
        response = client.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                'Changes': [
                    {
                        'Action': action,
                        'ResourceRecordSet': {
                            'Name': record_name,
                            'Type': record_type,
                            'TTL': 180,
                            'ResourceRecords': [{'Value': record_value}]
                        }
                    }
                ]
            }
        )
        return {
            'statusCode': 200,
            'body': json.dumps(response, cls=DateTimeEncoder)
        }
    except Exception as e: # pragma: no cover
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps(str(e), cls=DateTimeEncoder)
        }

def lambda_handler(event, context):
    print(event)
    message = json.loads(event["Records"][0]["Sns"]["Message"])
    dns_zone = message.get("dns_zone")
    action = message.get("action")
    zone_id = get_hosted_zone_id(dns_zone)
    if zone_id:
        if action == "create" or action == "update":
            return change_resource_record(message["record_name"], message["record_type"], message["record_value"], zone_id, "UPSERT")
        elif action == "delete":
            return change_resource_record(message["record_name"], message["record_type"], message["record_value"], zone_id, "DELETE")
    return {
        'statusCode': 500,
        'body': json.dumps({
            "Status": "{} not found".format(dns_zone)
        })
    }

