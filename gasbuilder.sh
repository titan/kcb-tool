#! /usr/bin/sh

BASE=`dirname $0`

echo "Building gas"
$BASE/dbtool.py -db -gt -3c $1 gas
echo "Done"
