#!/bin/bash

# Clone the destination repository
git clone https://github.com/icarus612/maze-runner-mono.git dest-repo

# Copy the content from all the source paths to the destination repository
cp -R  daedalus-mono/apps/flask/maze-runner/ dest-repo/apps/flask 2>/dev/null
cp -R  daedalus-mono/apps/next/maze-runner/ dest-repo/apps/next 2>/dev/null

cp -R  daedalus-mono/libs/python/maze-runner/ dest-repo/libs/python 2>/dev/null
cp -R  daedalus-mono/libs/javascript/node/maze-runner/ dest-repo/libs/javascript 2>/dev/null
cp -R  daedalus-mono/libs/javascript/react/maze-runner/ dest-repo/libs/react-js 2>/dev/null
cp -R  daedalus-mono/libs/javascript/solid/maze-runner/ dest-repo/libs/solid-js 2>/dev/null

# Push destination repository
cd dest-repo
git config user.name github-actions
git config user.email github-actions@github.com
git add .
git commit -m "Sync content from source repository"
git push