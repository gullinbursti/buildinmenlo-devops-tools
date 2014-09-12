from os import path
from distutils.core import setup

setup(
    name='buildinmenlo-devops-tools',
    version='0.1.0',
    author='Pedro H',
    author_email='pedro@builtinmenlo.com',
    scripts=[
        path.join('reporting', 'db-45-day-report.py'),
        path.join('reporting', 'keen-event-collection-action-info.py'),
        path.join('reporting', 'keen-event-collection-info.py')])
