#!/usr/bin/env bash

if ! command -v docker &> /dev/null; then
    echo "`docker` could not be found"
    exit 1
fi

if test $# -lt 1; then
    echo "Usage: $0 path/to/strava/activities [OPTIONS]"
    exit 1
fi

ACTIVITIES_DIR=$(realpath "$1")
shift

IMAGE="strava"
docker build -t ${IMAGE} . > /dev/null
docker run -it --rm \
    -u $(id -u):$(id -g) \
    -v $(pwd):/app \
    -v ${ACTIVITIES_DIR}:/activities:ro \
    ${IMAGE} \
    --gpx-dir /activities \
    "$@"
