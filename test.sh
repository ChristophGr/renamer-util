#!/bin/bash
IFS='
'
if [ -z "$1" ]; then
	FOLDER=/media/truecrypt1/Serien
else
	FOLDER=$1
fi

for x in `ls -1 $FOLDER`; do
	test -d "$FOLDER/$x" || continue;
    echo $x
	$PWD/rename.py "$FOLDER/$x"
done
