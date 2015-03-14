#! /usr/bin/sh

BASE=`dirname $0`

echo "Building lng..."
$BASE/dbtool.py -db -gt -3c $1 lng
echo "Done"
