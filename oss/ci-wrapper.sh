#!/bin/bash
cd /master/oss
ls -al
#mkdir -p /master/oss/dist
#chmod a+w /master/oss/dist
#ls -al
python3 generator/build.py --build 5.4.3
