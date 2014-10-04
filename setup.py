from os import path
from setuptools import setup

setup(
    name='buildinmenlo-devops-tools',
    version='0.3.1',
    author='Pedro H',
    author_email='pedro@builtinmenlo.com',
    install_requires=[
        'MySQL-python>=1.2.5',
        'Padding>=0.4',
        'boto>=2.32.1',
        'certifi>=14.05.14',
        'colorlog>=2.4.0',
        'elasticsearch<1.0.0',
        'keen>=0.3.0',
        'pycrypto>=2.6.1',
        'python-dateutil>=2.2',
        'requests>=2.4.0',
        'six>=1.8.0',
        'wsgiref>=0.1.2'],
    entry_points={'console_scripts': [
        'delete-user = bimadmin.selfieclub.deleteuser:main',
        'create_ec2_instance_alarms = bimadmin.aws.cloudwatch.ec2:create',
        'create_elasticache_instance_alarms = bimadmin.aws.cloudwatch.elasticache:create',  # noqa
        'create_elb_alarms = bimadmin.aws.cloudwatch.elb:create',
        'create_rds_instance_alarms = bimadmin.aws.cloudwatch.rds:create',
    ]},
    scripts=[
        # TODO: Convert to modules and move to 'console_scripts'.
        path.join('scripts', 'reporting', 'active-user-report.py'),
        path.join('scripts', 'reporting', 'db-45-day-report.py'),
        path.join('scripts', 'reporting',
                  'keen-event-collection-action-info.py'),
        path.join('scripts', 'reporting', 'keen-event-collection-info.py')])
