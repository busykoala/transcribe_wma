#!/usr/bin/env bash

docker build --platform linux/amd64 -t transcribe:latest .
docker save -o transcribe.tar transcribe:latest
scp transcribe.tar rootServer:/tmp/transcribe.tar
ssh rootServer "docker load < /tmp/transcribe.tar"
ssh rootServer "rm -rf /tmp/transcribe.tar"
rm -f transcribe.tar
