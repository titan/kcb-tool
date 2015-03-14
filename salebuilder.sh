#! /usr/bin/sh

BASE=`dirname $0`

echo "Building sale..."
$BASE/dbtool.py -db -gt -3c -mk $1 sale
echo "Done"
