#!/bin/bash
#set -x 

if [[ -z $1 ]]
then
    echo "usage: $0 [directory]"
    exit -1
fi

find $1 -print | while read filename; do
    # do whatever you want with the file
    TIMESTAMP=$(date +%s)
    TIMESTAMP_FILE=$(date +%s -r "$filename")
    #update modification time if file is older than 4 weeks
    if [[ $((TIMESTAMP-TIMESTAMP_FILE)) -gt 2419200  ]]
    then
       echo $filename
       touch -d "$(date -R -r "$filename") + 28 days" "$filename"
    fi
done
