#!/usr/bin/bash

cd ~/ros2

. install/setup.bash

ros2 launch slicer visual_launch.py

ros2 topic echo trigger | while read line
do
  if [[ "$line" == *"Done"* ]]
  then
    ros2 node kill --all
  fi
done
