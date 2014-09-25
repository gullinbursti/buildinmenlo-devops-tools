#! /usr/bin/env python
# pylint: disable=global-statement, duplicate-code
# TODO - eliminate:
#    - global-statement
#    - duplicate-code

import ConfigParser
import argparse
import boto.ec2
import boto.ec2.cloudwatch
import boto.rds2
import logging
import os

AWS_REGION = None
AWS_SNS_TOPIC = None
AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None

CONFIG_SECTION = 'aws'
CONFIG_FILE = os.path.join(
    os.environ['HOME'], '.builtinmenlo', 'devops-tools.cnf')
LOG_LEVEL = logging.INFO
CLOUDWATCH_NAME_PREFIX = 'elb'


def create():
    logging.basicConfig(level=LOG_LEVEL)
    read_configuration()
    args = process_args()
    process_instances(args.balancer_names)


def process_instances(balancer_names):
    cloudwatch_conn = boto.ec2.cloudwatch.connect_to_region(
        AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    for balancer_name in balancer_names:
        process_instance(cloudwatch_conn, balancer_name)


def process_instance(cloudwatch_conn, balancer_name):
    create_unhealthyhostcount_alarm(cloudwatch_conn, balancer_name)
    create_healthyhostcount_alarm(cloudwatch_conn, balancer_name)


def create_healthyhostcount_alarm(cloudwatch_conn, balancer_name):
    name = "{}+{}+HealthyHostCount".format(CLOUDWATCH_NAME_PREFIX,
                                           balancer_name)
    logging.info("Processing: %s", name)
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection=cloudwatch_conn,
        name=name,
        description="Elastic Load Balancers check healthy host count check "
        "for '{}'".format(balancer_name),
        metric='HealthyHostCount',
        namespace='AWS/ELB',
        statistic='Average',
        comparison='<',
        threshold=1,
        period=300,
        evaluation_periods=3,
        dimensions={'LoadBalancerName': balancer_name},
        alarm_actions=[AWS_SNS_TOPIC],
        ok_actions=[AWS_SNS_TOPIC],
        insufficient_data_actions=[AWS_SNS_TOPIC])
    cloudwatch_conn.put_metric_alarm(alarm)


def create_unhealthyhostcount_alarm(cloudwatch_conn, balancer_name):
    name = "{}+{}+UnHealthyHostCount".format(CLOUDWATCH_NAME_PREFIX,
                                             balancer_name)
    logging.info("Processing: %s", name)
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection=cloudwatch_conn,
        name=name,
        description="Elastic Load Balancers check unhealthy host count check "
        "for '{}'".format(balancer_name),
        metric='UnHealthyHostCount',
        namespace='AWS/ELB',
        statistic='Average',
        comparison='>=',
        threshold=1,
        period=300,
        evaluation_periods=3,
        dimensions={'LoadBalancerName': balancer_name},
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
        description='Setup AWS ClousWatch alarms for Elastic Load Balancers.')
    parser.add_argument(
        'balancer_names',
        metavar='BALANCE_NAME',
        nargs='+',
        help='load balancer name(s)')
    return parser.parse_args()
