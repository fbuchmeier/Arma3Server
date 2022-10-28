#!/bin/sh

# Copy steamcmd to VOLUME to allow read only root filesystem
mkdir -p /steamcmd
cp -a /opt/steamcmd/* /steamcmd/

mkdir /arma3/logs

exec "$@"
