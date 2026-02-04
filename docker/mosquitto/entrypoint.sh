#!/bin/sh
set -e

mkdir -p /mosquitto/data /mosquitto/log
chown -R mosquitto:mosquitto /mosquitto/data /mosquitto/log

exec "$@"
