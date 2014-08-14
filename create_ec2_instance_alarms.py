#! /usr/bin/env python

import boto.ec2.cloudwatch
import sys
import os

AWS_REGION = os.environ.get("AWS_EC2_REGION", "us-east-1")
TOPIC = 'arn:aws:sns:us-east-1:892810128873:00-ops-selfieclub-monitoring'


def alarm_name_prefix(instance_name):
    prefix_list = instance_name.split('.')
    prefix_list.reverse()
    prefix = '.'.join(prefix_list)
    return prefix


def get_instance_info(instance_id):
    ec2_conn = boto.ec2.connect_to_region(AWS_REGION)
    reservations = ec2_conn.get_all_instances(filters = {'instance-id': instance_id})

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
        connection = cloudwatch_conn,
        name = name,
        metric = 'StatusCheckFailed',
        namespace = 'AWS/EC2',
        statistic = 'Maximum',
        comparison = '>=',
        description = 'Status check for {} ({})'.format(instance_info['id'], instance_info['name']),
        threshold = 1.0,
        period = 300,
        evaluation_periods = 3,
        dimensions = {'InstanceId':instance_info['id']},
        alarm_actions = [TOPIC],
        ok_actions = [TOPIC],
        insufficient_data_actions = [TOPIC])
    cloudwatch_conn.put_metric_alarm(alarm)


def create_cpu_alarm(cloudwatch_conn, instance_info):
    name = "{}+CPUUtilization".format(instance_info['name_prefix'])
    print("Processing: {}".format(name))
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection = cloudwatch_conn,
        name = name,
        description = 'CPU utilization check for {} ({})'.format(instance_info['id'], instance_info['name']),
        metric = 'CPUUtilization',
        namespace = 'AWS/EC2',
        statistic = 'Average',
        comparison = '>=',
        threshold = 70.0,
        period = 300,
        evaluation_periods = 3,
        dimensions = {'InstanceId':instance_info['id']},
        alarm_actions = [TOPIC],
        ok_actions = [TOPIC],
        insufficient_data_actions = [TOPIC])
    cloudwatch_conn.put_metric_alarm(alarm)


def create_swap_alarm(cloudwatch_conn, instance_info):
    name = "{}+SwapUtilization".format(instance_info['name_prefix'])
    print("Processing: {}".format(name))
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection = cloudwatch_conn,
        name = name,
        description = 'Swap utilization check for {} ({})'.format(instance_info['id'], instance_info['name']),
        metric = 'SwapUtilization',
        namespace = 'System/Linux',
        statistic = 'Average',
        comparison = '>=',
        threshold = 90.0,
        period = 300,
        evaluation_periods = 3,
        dimensions = {'InstanceId':instance_info['id']},
        alarm_actions = [TOPIC],
        ok_actions = [TOPIC],
        insufficient_data_actions = [TOPIC])
    cloudwatch_conn.put_metric_alarm(alarm)


def create_memory_alarm(cloudwatch_conn, instance_info):
    name = "{}+MemoryUtilization".format(instance_info['name_prefix'])
    print("Processing: {}".format(name))
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection = cloudwatch_conn,
        name = name,
        description = 'Swap utilization check for {} ({})'.format(instance_info['id'], instance_info['name']),
        metric = 'MemoryUtilization',
        namespace = 'System/Linux',
        statistic = 'Average',
        comparison = '>=',
        threshold = 50.0,
        period = 300,
        evaluation_periods = 3,
        dimensions = {'InstanceId':instance_info['id']},
        alarm_actions = [TOPIC],
        ok_actions = [TOPIC],
        insufficient_data_actions = [TOPIC])
    cloudwatch_conn.put_metric_alarm(alarm)


def create_disk_alarm(cloudwatch_conn, instance_info):
    name = "{}+DiskSpaceUtilization".format(instance_info['name_prefix'])
    print("Processing: {}".format(name))
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection = cloudwatch_conn,
        name = name,
        description = 'Disk space utilization check for {} ({})'.format(instance_info['id'], instance_info['name']),
        metric = 'DiskSpaceUtilization',
        namespace = 'System/Linux',
        statistic = 'Average',
        comparison = '>=',
        threshold = 70.0,
        period = 300,
        evaluation_periods = 3,
        dimensions = {'InstanceId':instance_info['id'], 'Filesystem':'/dev/xvda1', 'MountPath':'/' },
        alarm_actions = [TOPIC],
        ok_actions = [TOPIC],
        insufficient_data_actions = [TOPIC])
    cloudwatch_conn.put_metric_alarm(alarm)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: create_status_alarm.py <instanceid>"
        sys.exit(2)
    instance_id = sys.argv[1]
    instance_info = get_instance_info(instance_id)

    cloudwatch_conn = boto.ec2.cloudwatch.connect_to_region(AWS_REGION)
    create_status_alarm(cloudwatch_conn, instance_info)
    create_cpu_alarm(cloudwatch_conn, instance_info)
    create_swap_alarm(cloudwatch_conn, instance_info)
    create_memory_alarm(cloudwatch_conn, instance_info)
    create_disk_alarm(cloudwatch_conn, instance_info)
    cloudwatch_conn.close()
