#! /usr/bin/env python

import ConfigParser
import argparse
import boto.ec2
import boto.ec2.cloudwatch
import boto.rds2
import logging
import os
import sys

AWS_REGION = None
AWS_SNS_TOPIC = None
AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None

CONFIG_SECTION = 'aws'
CONFIG_FILE = os.path.join(
    os.environ['HOME'], '.builtinmenlo', 'devops-tools.cnf')
LOG_LEVEL = logging.INFO
LOG_FILE = 'create_rds_instance_alarms.log'
FREEABLE_MEMORY_RATIO = 0.15
FREE_STORAGE_SPACE_RATIO = 0.20
CLOUDWATCH_NAME_PREFIX = 'rds'

EC2_INSTANCE_INFO = {
    'db.t2.micro': {
        'memory': 1000000000  # 1 GB
    }
}


def main():
    logging.basicConfig(level=LOG_LEVEL)
    read_configuration()
    args = process_args()
    process_instances(args.instance_ids)


def process_instances(instance_ids):
    cloudwatch_conn = boto.ec2.cloudwatch.connect_to_region(
        AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    for instance_id in instance_ids:
        process_instance(cloudwatch_conn, instance_id)


def process_instance(cloudwatch_conn, instance_id):
    instance_info = get_instance_info(instance_id)
    create_cpu_alarm(cloudwatch_conn, instance_info)
    create_freeablememory_alarm(cloudwatch_conn, instance_info)
    create_freestoragespace_alarm(cloudwatch_conn, instance_info)


def get_instance_info(instance_id):
    rds_conn = boto.rds2.connect_to_region(
        AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    response = rds_conn.describe_db_instances(
        db_instance_identifier=instance_id)
    # TODO - pep8 ignore line length
    response = response['DescribeDBInstancesResponse']
    dbinstance = response['DescribeDBInstancesResult']['DBInstances'][0]
    if not dbinstance:
        print "Invalid instance-id!"
        sys.exit(1)
    instance_class = dbinstance['DBInstanceClass']
    memory = EC2_INSTANCE_INFO[instance_class]['memory']
    return {
        'instance_id': instance_id,
        'allocated_storage': dbinstance['AllocatedStorage'] * 1000000000,
        'memory': memory
    }


def create_freestoragespace_alarm(cloudwatch_conn, instance_info):
    name = "{}+{}+FreeStorageSpace".format(CLOUDWATCH_NAME_PREFIX,
                                           instance_info['instance_id'])
    logging.info("Processing: %s", name)
    limit = round(float(instance_info['allocated_storage'])
                  * FREE_STORAGE_SPACE_RATIO)
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection=cloudwatch_conn,
        name=name,
        description="RDS MySQL free storage check for '{}'".format(
            instance_info['instance_id']),
        metric='FreeStorageSpace',
        namespace='AWS/RDS',
        statistic='Average',
        comparison='<=',
        threshold=limit,
        period=300,
        evaluation_periods=3,
        dimensions={'DBInstanceIdentifier': instance_info['instance_id']},
        alarm_actions=[AWS_SNS_TOPIC],
        ok_actions=[AWS_SNS_TOPIC],
        insufficient_data_actions=[AWS_SNS_TOPIC])
    cloudwatch_conn.put_metric_alarm(alarm)


def create_cpu_alarm(cloudwatch_conn, instance_info):
    name = "{}+{}+CPUUtilization".format(CLOUDWATCH_NAME_PREFIX,
                                         instance_info['instance_id'])
    logging.info("Processing: %s", name)
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection=cloudwatch_conn,
        name=name,
        description="RDS MySQL CPU utilization check for '{}'".format(
            instance_info['instance_id']),
        metric='CPUUtilization',
        namespace='AWS/RDS',
        statistic='Average',
        comparison='>=',
        threshold=70.0,
        period=300,
        evaluation_periods=3,
        dimensions={'DBInstanceIdentifier': instance_info['instance_id']},
        alarm_actions=[AWS_SNS_TOPIC],
        ok_actions=[AWS_SNS_TOPIC],
        insufficient_data_actions=[AWS_SNS_TOPIC])
    cloudwatch_conn.put_metric_alarm(alarm)


def create_freeablememory_alarm(cloudwatch_conn, instance_info):
    name = "{}+{}+FreeableMemory".format(CLOUDWATCH_NAME_PREFIX,
                                         instance_info['instance_id'])
    logging.info("Processing: %s", name)
    limit = round(float(instance_info['memory']) * FREEABLE_MEMORY_RATIO)
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection=cloudwatch_conn,
        name=name,
        description="RDS MySQL freeable memory check for '{}'".format(
            instance_info['instance_id']),
        metric='FreeableMemory',
        namespace='AWS/RDS',
        statistic='Average',
        comparison='<=',
        threshold=limit,
        period=300,
        evaluation_periods=3,
        dimensions={'DBInstanceIdentifier': instance_info['instance_id']},
        alarm_actions=[AWS_SNS_TOPIC],
        ok_actions=[AWS_SNS_TOPIC],
        insufficient_data_actions=[AWS_SNS_TOPIC])
    cloudwatch_conn.put_metric_alarm(alarm)


def read_configuration():
    logging.debug("Reading configuration: %s[%s]", CONFIG_FILE, CONFIG_SECTION)

    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)

    global AWS_REGION, AWS_SNS_TOPIC, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    AWS_REGION = config.get(CONFIG_SECTION, 'aws_region')
    AWS_SNS_TOPIC = config.get(CONFIG_SECTION, 'aws_sns_topic')
    AWS_ACCESS_KEY_ID = config.get(CONFIG_SECTION, 'aws_access_key_id')
    AWS_SECRET_ACCESS_KEY = config.get(CONFIG_SECTION, 'aws_secret_access_key')

    logging.info("Configuration: %s", {
        'aws_region': AWS_REGION,
        'aws_sns_topic': AWS_SNS_TOPIC,
        'aws_access_key_id': 'XXXXXXXX',
        'aws_secret_access_key': 'YYYYYYYY'})


def process_args():
    parser = argparse.ArgumentParser(
        description='Setup AWS ClousWatch alarms for RDS MySQL instances.')
    parser.add_argument(
        'instance_ids',
        metavar='INSTANCE_ID',
        nargs='+',
        help='RDS database insance identifier')
    return parser.parse_args()


if __name__ == "__main__":
    main()
