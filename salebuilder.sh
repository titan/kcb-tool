#! /usr/bin/sh

BASE=`dirname $0`

echo "Building sale..."
$BASE/dbtool.py -db -gt -mk $1 sale
echo "Done"
