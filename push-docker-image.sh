#!/bin/bash

VERSION=v1
IMAGE_NAME=grafana/grafana-oss-ci-msi-build
git lfs pull

docker build -t ${IMAGE_NAME}:latest -t ${IMAGE_NAME}:${VERSION} --no-cache=true .

docker login
docker push ${IMAGE_NAME}:latest
docker push ${IMAGE_NAME}:${VERSION}

