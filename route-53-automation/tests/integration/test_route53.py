import os, boto3, pytest, time

class TestRoute53:

    @pytest.fixture()
    def outputs_cloudformation(self):
        client = boto3.client("sts")
        response = client.get_caller_identity()

        """Get the SNS ARN from CloudFormation Stack Outputs"""
        stack_name = os.environ.get("AWS_SAM_STACK_NAME")

        if stack_name is None:
            raise ValueError("Please set the AWS_SAM_STACK_NAME environment variable")

        client = boto3.client("cloudformation")

        try:
            response =  client.describe_stacks(StackName=stack_name)
        except Exception as e:
            raise Exception(
                f"Cannot find stack {stack_name}\n"
            ) from e

        stacks = response["Stacks"]
        stacks_outputs = stacks[0]["Outputs"]
        infra_outputs = { output["OutputKey"] : output["OutputValue"] for output in stacks_outputs }

        if not infra_outputs:
            raise KeyError(f"Outputs not found ")

        return infra_outputs

    def test_add_record(self, outputs_cloudformation):
        client_sns = boto3.client("sns")
        client_r53 = boto3.client("route53")
        response = client_sns.publish(
            TopicArn=outputs_cloudformation["SNSTopicArn"],
            Message="{\n \"action\": \"create\",\n \"record_name\": \"integrationtest.dev.fabririvas.com\",\n \"dns_zone\": \"dev.fabririvas.com\",\n  \"record_type\": \"A\",\n  \"record_value\": \"10.0.0.2\"\n}",
            Subject="Integration Test"
        )
        print(response)
        time.sleep(2)
        record_sets = client_r53.list_resource_record_sets(HostedZoneId=outputs_cloudformation["HostedZoneId"])
        records = record_sets['ResourceRecordSets']
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert any(record for record in records if record['Name'] == 'integrationtest.dev.fabririvas.com.' and record['Type'] == 'A' and record['ResourceRecords'][0]['Value'] == '10.0.0.2')

    def test_delete_record(self, outputs_cloudformation):
        client_sns = boto3.client("sns")
        client_r53 = boto3.client("route53")
        response = client_sns.publish(
            TopicArn=outputs_cloudformation["SNSTopicArn"],
            Message="{\n \"action\": \"delete\",\n \"record_name\": \"integrationtest.dev.fabririvas.com\",\n \"dns_zone\": \"dev.fabririvas.com\",\n  \"record_type\": \"A\",\n  \"record_value\": \"10.0.0.2\"\n}",
            Subject="Integration Test"
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        print(response)
        time.sleep(1)
        record_sets = client_r53.list_resource_record_sets(HostedZoneId=outputs_cloudformation["HostedZoneId"])
        records = [record["Name"] for record in record_sets['ResourceRecordSets']]
        assert "integrationtest.dev.fabririvas.com." not in records

