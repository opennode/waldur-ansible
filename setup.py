#!/usr/bin/env python
from setuptools import setup, find_packages


tests_requires = [
    'ddt>=1.0.0',
    'factory_boy==2.4.1',
    'mock>=1.0.1',
]

install_requires = [
    'waldur-core>=0.151.0',
    'waldur-openstack>=0.38.2',
]


setup(
    name='waldur-ansible',
    version='0.4.0',
    author='OpenNode Team',
    author_email='info@opennodecloud.com',
    url='https://waldur.com',
    description='Waldur plugin for Ansible playbooks management and execution.',
    long_description=open('README.rst').read(),
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=install_requires,
    zip_safe=False,
    extras_require={
        'tests': tests_requires,
    },
    entry_points={
        'waldur_extensions': (
            'waldur_playbook_jobs = waldur_ansible.playbook_jobs.extension:PlaybookJobsExtension',
            'waldur_python_management = waldur_ansible.python_management.extension:PythonManagementExtension',
        ),
    },
    include_package_data=True,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
)
