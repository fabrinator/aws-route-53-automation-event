import json, pytest, boto3
from moto import mock_aws
from src import app
from .events import sns_json_file
from datetime import datetime


@pytest.fixture(scope='module')
def create_dns_zone():
    with mock_aws():
        conn = boto3.client("route53")
        testZone = conn.create_hosted_zone(
            Name = "unittest.fabririvas.com",
            HostedZoneConfig = {
                "Comment": "Domain for unittest.fabririvas.com",
                "PrivateZone": False
            },
            CallerReference="unittest"
        )
        zoneId = testZone["HostedZone"]["Id"].split("/")[-1]
        yield zoneId

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@mock_aws
def test_lambda_handler_create(create_dns_zone):
    conn = boto3.client("route53")
    zoneId = create_dns_zone
    sns_event = sns_json_file()
    sns_event["Records"][0]["Sns"]["Message"] = "{\n \"action\": \"add\",\n \"record_name\": \"record.unittest.fabririvas.com\",\n \"dns_zone\": \"unittest.fabririvas.com\",\n  \"record_type\": \"A\",\n  \"record_value\": \"10.0.0.1\"\n}"
    ret = app.lambda_handler(sns_event, "")
    record_sets = conn.list_resource_record_sets(HostedZoneId=zoneId)
    records = record_sets['ResourceRecordSets']
    data = json.loads(ret["body"])
    assert data["ChangeInfo"]["Status"] == "PENDING" or "INSYNC"
    assert ret["statusCode"] == 200
    assert any(record for record in records if record['Name'] == 'record.unittest.fabririvas.com.' and record['Type'] == 'A' and record['ResourceRecords'][0]['Value'] == '10.0.0.1')

@mock_aws
def test_lambda_handler_host_zone_not_exists(create_dns_zone):
    sns_event = sns_json_file()
    sns_event["Records"][0]["Sns"]["Message"] = "{\n \"action\": \"add\",\n \"record_name\": \"record.nodomain.fabririvas.com\",\n \"dns_zone\": \"nodomain.fabririvas.com\",\n  \"record_type\": \"A\",\n  \"record_value\": \"10.0.0.1\"\n}"
    ret = app.lambda_handler(sns_event, "")
    body = json.loads(ret["body"])
    assert ret["statusCode"] == 500
    assert body["Status"] == "nodomain.fabririvas.com not found"

@mock_aws
def test_lambda_handler_delete(create_dns_zone):
    sns_event = sns_json_file()
    sns_event["Records"][0]["Sns"]["Message"] = "{\n \"action\": \"delete\",\n \"record_name\": \"record.unittest.fabririvas.com\",\n \"dns_zone\": \"unittest.fabririvas.com\",\n  \"record_type\": \"A\",\n  \"record_value\": \"10.0.0.1\"\n}"
    ret = app.lambda_handler(sns_event, "")
    data = json.loads(ret["body"])
    assert data["ChangeInfo"]["Status"] == "PENDING" or "INSYNC"
    assert ret["statusCode"] == 200