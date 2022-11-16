#!/bin/bash

set -e

npm --version

npm install --omit=dev

# always exit with 0 here
npm audit fix --omit=dev || echo
npm audit signatures --omit=dev
