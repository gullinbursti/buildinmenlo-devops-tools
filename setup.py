from os import path
from distutils.core import setup

setup(
    name='buildinmenlo-devops-tools',
    version='0.2.0',
    author='Pedro H',
    author_email='pedro@builtinmenlo.com',
    scripts=[
        path.join('scripts', 'aws', 'create_ec2_instance_alarms.py'),
        path.join('scripts', 'aws', 'create_elasticache_instance_alarms.py'),
        path.join('scripts', 'aws', 'create_elb_alarms.py'),
        path.join('scripts', 'aws', 'create_rds_instance_alarms.py'),
        path.join('scripts', 'reporting', 'db-45-day-report.py'),
        path.join('scripts', 'reporting',
                  'keen-event-collection-action-info.py'),
        path.join('scripts', 'reporting', 'keen-event-collection-info.py'),
        path.join('scripts', 'selfieclub-admin', 'delete-user.py')])
