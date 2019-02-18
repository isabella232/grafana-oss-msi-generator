#!/bin/bash
ls -l /master
cd oss
# nssm download has been unreliable, use a cached copy of it
mkdir -p /tmp/cache
cp cache/nssm-2.24.zip /tmp/cache
python3 generator/build.py --build 5.4.3
