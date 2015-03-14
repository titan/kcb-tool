#! /usr/bin/sh

BASE=`dirname $0`

echo "Building model..."
$BASE/dbtool.py -db -1c $1 model
echo "Done"
