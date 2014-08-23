#! /usr/bin/env python

import boto.ec2.cloudwatch
import sys
import os
import logging
import ConfigParser
import argparse

AWS_REGION = None
AWS_SNS_TOPIC = None
AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None

CONFIG_SECTION = 'aws'
CONFIG_FILE = os.path.join(
    os.environ['HOME'], '.builtinmenlo', 'devops-tools.cnf')
LOG_LEVEL = logging.INFO

AWS_REGION = os.environ.get("AWS_EC2_REGION", "us-east-1")
TOPIC = 'arn:aws:sns:us-east-1:892810128873:00-ops-selfieclub-monitoring'


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
    cloudwatch_conn.close()


def process_instance(cloudwatch_conn, instance_id):
    instance_info = get_instance_info(instance_id)
    cloudwatch_conn = boto.ec2.cloudwatch.connect_to_region(AWS_REGION)
    create_status_alarm(cloudwatch_conn, instance_info)
    create_cpu_alarm(cloudwatch_conn, instance_info)
    create_swap_alarm(cloudwatch_conn, instance_info)
    create_memory_alarm(cloudwatch_conn, instance_info)
    create_disk_alarm(cloudwatch_conn, instance_info)


def alarm_name_prefix(instance_name):
    prefix_list = instance_name.split('.')
    prefix_list.reverse()
    prefix = '.'.join(prefix_list)
    return prefix


def get_instance_info(instance_id):
    ec2_conn = boto.ec2.connect_to_region(AWS_REGION)
    reservations = ec2_conn.get_all_instances(
        filters={'instance-id': instance_id})

    if not (reservations and reservations[0].instances):
        print "Invalid instance-id!"
        sys.exit(1)

    instance = reservations[0].instances[0]
    instance_name = instance.tags['Name']
    instance_info = dict(
        id=instance_id,
        name=instance_name,
        name_prefix=alarm_name_prefix(instance_name),
    )

    return instance_info


def create_status_alarm(cloudwatch_conn, instance_info):
    name = "{}+StatusCheckFailed".format(instance_info['name_prefix'])
    print("Processing: {}".format(name))
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection=cloudwatch_conn,
        name=name,
        metric='StatusCheckFailed',
        namespace='AWS/EC2',
        statistic='Maximum',
        comparison='>=',
        description="Status check for '{}' ({})".format(
            instance_info['id'], instance_info['name']),
        threshold=1.0,
        period=300,
        evaluation_periods=3,
        dimensions={'InstanceId': instance_info['id']},
        alarm_actions=[TOPIC],
        ok_actions=[TOPIC],
        insufficient_data_actions=[TOPIC])
    cloudwatch_conn.put_metric_alarm(alarm)


def create_cpu_alarm(cloudwatch_conn, instance_info):
    name = "{}+CPUUtilization".format(instance_info['name_prefix'])
    print("Processing: {}".format(name))
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection=cloudwatch_conn,
        name=name,
        description="CPU utilization check for '{}' ({})".format(
            instance_info['id'], instance_info['name']),
        metric='CPUUtilization',
        namespace='AWS/EC2',
        statistic='Average',
        comparison='>=',
        threshold=70.0,
        period=300,
        evaluation_periods=3,
        dimensions={'InstanceId': instance_info['id']},
        alarm_actions=[TOPIC],
        ok_actions=[TOPIC],
        insufficient_data_actions=[TOPIC])
    cloudwatch_conn.put_metric_alarm(alarm)


def create_swap_alarm(cloudwatch_conn, instance_info):
    name = "{}+SwapUtilization".format(instance_info['name_prefix'])
    print("Processing: {}".format(name))
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection=cloudwatch_conn,
        name=name,
        description="Swap utilization check for '{}' ({})".format(
            instance_info['id'], instance_info['name']),
        metric='SwapUtilization',
        namespace='System/Linux',
        statistic='Average',
        comparison='>=',
        threshold=90.0,
        period=300,
        evaluation_periods=3,
        dimensions={'InstanceId': instance_info['id']},
        alarm_actions=[TOPIC],
        ok_actions=[TOPIC],
        insufficient_data_actions=[TOPIC])
    cloudwatch_conn.put_metric_alarm(alarm)


def create_memory_alarm(cloudwatch_conn, instance_info):
    name = "{}+MemoryUtilization".format(instance_info['name_prefix'])
    print("Processing: {}".format(name))
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection=cloudwatch_conn,
        name=name,
        description="Swap utilization check for '{}' ({})".format(
            instance_info['id'], instance_info['name']),
        metric='MemoryUtilization',
        namespace='System/Linux',
        statistic='Average',
        comparison='>=',
        threshold=50.0,
        period=300,
        evaluation_periods=3,
        dimensions={'InstanceId': instance_info['id']},
        alarm_actions=[TOPIC],
        ok_actions=[TOPIC],
        insufficient_data_actions=[TOPIC])
    cloudwatch_conn.put_metric_alarm(alarm)


def create_disk_alarm(cloudwatch_conn, instance_info):
    name = "{}+DiskSpaceUtilization".format(instance_info['name_prefix'])
    print("Processing: {}".format(name))
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection=cloudwatch_conn,
        name=name,
        description="Disk space utilization check for '{}' ({})".format(
            instance_info['id'], instance_info['name']),
        metric='DiskSpaceUtilization',
        namespace='System/Linux',
        statistic='Average',
        comparison='>=',
        threshold=70.0,
        period=300,
        evaluation_periods=3,
        dimensions={
            'InstanceId': instance_info['id'],
            'Filesystem': '/dev/xvda1',
            'MountPath': '/'},
        alarm_actions=[TOPIC],
        ok_actions=[TOPIC],
        insufficient_data_actions=[TOPIC])
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
        description='Setup AWS ClousWatch alarms for EC2 instances.')
    parser.add_argument(
        'instance_ids',
        metavar='INSTANCE_ID',
        nargs='+',
        help='EC2 insance identifier(s)')
    return parser.parse_args()


if __name__ == '__main__':
    main()
