#! /usr/bin/env python

import ConfigParser
import argparse
import boto.elasticache
import boto.ec2.cloudwatch
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
UNUSED_MEMORY_RATIO = 0.10
CLOUDWATCH_NAME_PREFIX = 'elasticache'

EC2_INSTANCE_INFO = {
    'cache.t1.micro': {
        'memory': 1000000000  # 1 GB
    }
}


def main():
    logging.basicConfig(level=LOG_LEVEL)
    read_configuration()
    args = process_args()
    process_clusters(args.cluster_ids)


def process_clusters(cluster_ids):
    cloudwatch_conn = boto.ec2.cloudwatch.connect_to_region(
        AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    for cluster_id in cluster_ids:
        process_cluster(cloudwatch_conn, cluster_id)


def process_cluster(cloudwatch_conn, cluster_id):
    cluster_info = get_cluster_info(cluster_id)
    process_nodes(cloudwatch_conn, cluster_info)


def process_nodes(cloudwatch_conn, cluster_info):
    for node_id in cluster_info['node_ids']:
        node_info = {
            'cluster_id': cluster_info['cluster_id'],
            'node_id': node_id,
            'memory': cluster_info['memory']}
        create_cpu_alarm(cloudwatch_conn, node_info)
        create_unusedmemory_alarm(cloudwatch_conn, node_info)


def get_cluster_info(cluster_id):
    ec_conn = boto.elasticache.connect_to_region(
        AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    response = ec_conn.describe_cache_clusters(
        cache_cluster_id=cluster_id, show_cache_node_info=True)
    # TODO - pep8 ignore line length
    response = response['DescribeCacheClustersResponse']
    cluster = response['DescribeCacheClustersResult']['CacheClusters'][0]
    if not cluster:
        print "Invalid cluster-id!"
        sys.exit(1)
    nodes = []
    for node in cluster['CacheNodes']:
        nodes.append(node['CacheNodeId'])
    instance_class = cluster['CacheNodeType']
    memory = EC2_INSTANCE_INFO[instance_class]['memory']
    return {
        'cluster_id': cluster_id,
        'memory': memory,
        'node_ids': nodes}


def create_cpu_alarm(cloudwatch_conn, node_info):
    name = "{}+{}_{}+CPUUtilization".format(CLOUDWATCH_NAME_PREFIX,
                                            node_info['cluster_id'],
                                            node_info['node_id'])
    logging.info("Processing: %s", name)
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection=cloudwatch_conn,
        name=name,
        description="ElastiCache CPU utilization check for node '{}' in "
        "cluster '{}'".format(node_info["node_id"], node_info["cluster_id"]),
        metric='CPUUtilization',
        namespace='AWS/ElastiCache',
        statistic='Average',
        comparison='>=',
        threshold=70.0,
        period=300,
        evaluation_periods=3,
        dimensions={
            'CacheClusterId': node_info['cluster_id'],
            'CacheNodeId': node_info['node_id']},
        alarm_actions=[AWS_SNS_TOPIC],
        ok_actions=[AWS_SNS_TOPIC],
        insufficient_data_actions=[AWS_SNS_TOPIC])
    cloudwatch_conn.put_metric_alarm(alarm)


def create_unusedmemory_alarm(cloudwatch_conn, node_info):
    name = "{}+{}_{}+UnusedMemory".format(CLOUDWATCH_NAME_PREFIX,
                                          node_info['cluster_id'],
                                          node_info['node_id'])
    limit = round(float(node_info['memory']) * UNUSED_MEMORY_RATIO)
    logging.info("Processing: %s", name)
    alarm = boto.ec2.cloudwatch.alarm.MetricAlarm(
        connection=cloudwatch_conn,
        name=name,
        description="ElastiCache Unused memory utilization check for node "
        "'{}' in "
        "cluster '{}'".format(node_info["node_id"], node_info["cluster_id"]),
        metric='UnusedMemory',
        namespace='AWS/ElastiCache',
        statistic='Average',
        comparison='<=',
        threshold=limit,
        period=300,
        evaluation_periods=3,
        dimensions={
            'CacheClusterId': node_info['cluster_id'],
            'CacheNodeId': node_info['node_id']},
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
        description='Setup AWS ClousWatch alarms for RDS ElastiCache '
        'clusters.')
    parser.add_argument(
        'cluster_ids',
        metavar='CLUSTER_ID',
        nargs='+',
        help='ElastiCache cluster identifiers')
    return parser.parse_args()


if __name__ == "__main__":
    main()
