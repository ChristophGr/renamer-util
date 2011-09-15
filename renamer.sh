#!/bin/bash
IFS='
'
if [ -z "$1" ]; then
	echo missing folder
	exit 1
else
	FOLDER=$1
	echo "FOLDER=\"$FOLDER\""
fi

echo "iterating"
for x in `ls -1 $FOLDER`; do
	echo "testing $FOLDER/$x"
	test -d "$FOLDER/$x" || continue;
	echo $x
	$(dirname $0)/rename.py "$FOLDER/$x"
done
