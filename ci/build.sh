#!/bin/bash -ex

python3 -bb -X dev -W error pull.py fsf-api-build-output
cp -a assets/. fsf-api-build-output/
