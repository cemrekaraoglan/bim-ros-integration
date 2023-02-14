from setuptools import setup

import glob
import os

package_name = 'slicer'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'robot_model/meshes'), glob.glob('robot_model/meshes/*.dae')),
        (os.path.join('share', package_name, 'robot_model'), glob.glob('robot_model/robot_description2.urdf')),
        (os.path.join('share', package_name, 'launch'), glob.glob('launch/*.py')),
        (os.path.join('share', package_name, 'rviz'), glob.glob('config/rvitz_config.rviz')),
        (os.path.join('share', package_name, 'data'), glob.glob('wall_cut/output.txt')),
        (os.path.join('share', package_name, 'config'), glob.glob('config/param.yaml')) #place the file in the launch folder in this path and get it from this path

    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='beyzanurkaya',
    maintainer_email='beyzanur.kaya@rwth-aachen.de',
    description='Creates connection with IFC Model in server',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': ['slicer_cutter = slicer.main3:main', 'slicer_visualizer = slicer.main2:main', 'slicer = slicer.main:main'
        ],
    },
)
