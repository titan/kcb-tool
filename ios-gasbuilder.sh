#! /usr/bin/sh

BASE=`dirname $0`

echo "Building gas"
$BASE/dbtool.py -db -gt -ios $1 gas
echo "Done"
