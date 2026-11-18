from glob import glob
import os

from setuptools import setup

package_name = 'handheld_scanner_timesync'

setup(
    name=package_name,
    version='0.2.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='LaNHuii',
    maintainer_email='3186295108@qq.com',
    description='Read-only TimeSyncV2 USB CDC adapter for Handheld-scanner.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'handheld_scanner_timesync = '
            'handheld_scanner_timesync.node:main',
        ],
    },
)
