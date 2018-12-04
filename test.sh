#!/bin/bash

docker build -t dependabot.test --target test .
echo 'Test complete!'
