import os
from setuptools import setup, find_namespace_packages


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(
    name='kypo-terraform-client',
    author='MASARYK UNIVERSITY',
    description='KYPO Terraform Client',
    long_description=read('README.md'),
    packages=find_namespace_packages(include=['kypo.*'], exclude=['tests']),
    install_requires=[
        'kypo-python-commons==0.1.2',
        'kypo-openstack-lib==0.38.*',
    ],
    python_requires='>=3',
    zip_safe=False
)
