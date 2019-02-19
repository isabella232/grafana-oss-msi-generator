#!/bin/bash
ls -l /master
# when running circleci locally, need to change to oss directory
if [ -d oss ]; then
  cd oss
  ls -al
else
  # integrated circleci will have all of the code in /master
  # and the builds will be found in HOME
  pwd
  ls -al /home/xclient/repo/dist/
  mkdir -p /tmp/dist
  cp /home/xclient/repo/dist/*.zip /tmp/dist/
  ls -al /tmp/dist
  cd /master
  ls -al
fi
# nssm download has been unreliable, use a cached copy of it
mkdir -p /tmp/cache
cp cache/nssm-2.24.zip /tmp/cache
#python3 generator/build.py --build 5.4.3
python3 generator/build.py