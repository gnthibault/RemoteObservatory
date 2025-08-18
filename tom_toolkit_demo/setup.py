from setuptools import setup, find_packages


setup(
    name='tom_toolkit_demo',
    version='0.1',
    packages=find_packages(include=['observatory_server', 'data']),
    include_package_data=True,
    package_data={
        'data': ['*.txt', '*.csv', '*.json', '*.db'],# Include data files inside data/
    },
    description='A sample project with a data module',
    author='gnthibault', )

