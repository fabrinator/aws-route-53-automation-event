# aws-route-53-automation-event
sam deploy --capabilities CAPABILITY_NAMED_IAM --parameter-overrides Environment=dev

sam local invoke "Route53Function" -e events/sns.json