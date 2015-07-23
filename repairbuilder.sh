#! /usr/bin/sh

BASE=`dirname $0`

echo "Building repair..."
$BASE/dbtool.py -db -gt -mk $1 repair
echo "Done"
