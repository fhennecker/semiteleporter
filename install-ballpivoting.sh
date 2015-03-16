#!/bin/bash

pushd BallPivoting
cmake .
make -j2
popd

cp BallPivoting/ballpivoting src/ 
