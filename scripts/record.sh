#! /bin/sh

PRS_DIR=/home/yuiant/Projects/a/m/piano-rs/
BASEPATH=$(cd `dirname $0`; pwd)
cd $PRS_DIR && ./target/release/piano-rs -r $BASEPATH/saved/record.yml
