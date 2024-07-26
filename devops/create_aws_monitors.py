#########
# Create AWS Monitors for ArangoDB Cluster
#
# This script assumes all nodes of the ArangoDB Cluster are part of the same security group.
# All the instance IDs are fetched, and then alarms for CPU, RAM, and Disk are created for each EC2 instance.
# Alarms will notify a SNS Topic previously registered on AWS.
#
# Instructions:
# 1. Copy the Security Group ID where all EC2 instances of the cluster are part of into SECURITY_GROUP_ID.
# 2. Copy the SNS Topic name into SNS_TOPIC
# 3. Add the AWS region where the cluster is located into REGION.
# 4. If you have multiple profiles into your ~/.aws/credentials, select the one you wish the script to use
# 5. Run the script: python3 create_aws_monitors.py

import boto3

SECURITY_GROUP_ID = 'sg-0aa839f598f7841d3'  # dev
SNS_TOPIC = 'ArangoDBClusterAlarms'
REGION = 'us-west-2'
PROFILE_NAME = 'igvf-dev'


def create_alarms(session, instance_id):
    cloudwatch_client = session.client('cloudwatch')
    sns_client = session.client('sns')

    sns_topic_arn = sns_client.create_topic(Name=SNS_TOPIC)['TopicArn']

    try:
        alarms = [
            {
                'AlarmName': f'{instance_id}-igvf-catalog-CPU-Utilization-High',
                'MetricName': 'CPUUtilization',
                'Namespace': 'AWS/EC2',
                'Statistic': 'Average',
                'Dimensions': [
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                'Period': 300,
                'EvaluationPeriods': 2,
                'Threshold': 80.0,
                'ComparisonOperator': 'GreaterThanOrEqualToThreshold',
                'AlarmActions': [sns_topic_arn],
                'OKActions': [],
                'InsufficientDataActions': [],
                'Unit': 'Percent'
            },
            {
                'AlarmName': f'{instance_id}-igvf-catalog-Disk-Space-Utilization-High',
                'MetricName': 'disk_used_percent',
                'Namespace': 'AWS/EC2',
                'Statistic': 'Average',
                'Dimensions': [
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                'Period': 300,
                'EvaluationPeriods': 1,
                'Threshold': 90.0,
                'ComparisonOperator': 'GreaterThanOrEqualToThreshold',
                'AlarmActions': [sns_topic_arn],
                'OKActions': [],
                'InsufficientDataActions': [],
                'Unit': 'Bytes'
            },
            {
                'AlarmName': f'{instance_id}-igvf-catalog-RAM-Usage-High',
                'MetricName': 'mem_used_percent',
                'Namespace': 'CWAgent',
                'Statistic': 'Average',
                'Dimensions': [
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                'Period': 300,
                'EvaluationPeriods': 2,
                'Threshold': 80.0,
                'ComparisonOperator': 'GreaterThanOrEqualToThreshold',
                'AlarmActions': [sns_topic_arn],
                'OKActions': [],
                'InsufficientDataActions': [],
                'Unit': 'Percent'
            }
        ]

        for alarm in alarms:
            cloudwatch_client.put_metric_alarm(**alarm)
            print(f"Created alarm: {alarm['AlarmName']}")

    except Exception as e:
        print(f'An error occurred while creating alarms: {e}')


def get_instance_ids_from_security_group(session):
    ec2_client = session.client('ec2')

    try:
        response = ec2_client.describe_instances(Filters=[
            {
                'Name': 'instance.group-id',
                'Values': [SECURITY_GROUP_ID]
            }
        ])

        instance_ids = []
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance_ids.append(instance.get('InstanceId'))

        return instance_ids

    except Exception as e:
        print(f'An error occurred: {e}')
        return []


if __name__ == '__main__':
    session = boto3.Session(profile_name=PROFILE_NAME, region_name=REGION)

    instance_ids = get_instance_ids_from_security_group(session)

    if instance_ids:
        for instance_id in instance_ids:
            create_alarms(session, instance_id)
    else:
        print('No instance IDs found or an error occurred.')
