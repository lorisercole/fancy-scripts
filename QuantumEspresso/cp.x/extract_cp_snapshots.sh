#!/usr/bin/env bash

function usage
{
   echo "This script extracts snapshots from a .pos CP file."
   echo "Usage:  extract_cp_snapshots.sh -f POS_FILE [-h]"
   echo "         -f POS_FILE  CP trajectory file"
   echo "         --first FIRST_STEP"
   echo "         --delta DELTA_STEP"
   echo "         --last  LAST_STEP"
   echo "         --no-list       do not print the list of snapshots"
   echo "         --list  SNAPSHOTS_LIST    name of the snapshots list"
   echo "         -h  --help      print this help"
   echo "Example:  extract_cp_snapshots.sh -f POS_FILE -first 100 -delta 10 -last 200 [-h]"
}

POS_FILE=
FIRST_STEP=0
LAST_STEP=99999999
DELTA_STEP=1
LIST=1
LIST_NAME='snapshots_list'

while [ $# -gt 0 ]; do
    case $1 in
        -f )              shift; POS_FILE=$1
                          ;;
        --first )         shift; FIRST_STEP=$1
                          ;;
        --delta )         shift; DELTA_STEP=$1
                          ;;
        --last )          shift; LAST_STEP=$1
                          ;;
        --no-list )       LIST=0
                          ;;
        --list )          shift; LIST_NAME=$1
                          ;;
        -h | --help )     usage
                          exit
                          ;;
        * )               usage
                          exit 1
    esac
    shift
done

if [[ ( (-z "$POS_FILE") ) ]]; then
   usage
   exit 1
fi

mkdir snapshots
PREFIX=snapshots/${POS_FILE%.*}
SUBFIX=${POS_FILE##*.}

awk -vfirst=$FIRST_STEP -vlast=$LAST_STEP -vdelta=$DELTA_STEP -vprefix=$PREFIX -vsubfix=$SUBFIX -vlist=$LIST -vlistname=$LIST_NAME '
(NF == 2) && ($1 >= first) && ($1 <= last){
  if (($1-first)%delta == 0) {
    step = $1
    print $1, $2 >> sprintf("%s_step_%d.%s", prefix, step, subfix)
    if (list)
      print step >> listname
    print step
    flag = 1
  }
  else {
    flag = 0
  }
}
(NF == 2) && ($1 > last){
  flag = 0
}
(NF == 3) && flag {
    print >> sprintf("%s_step_%d.%s", prefix, step, subfix)
}
' $POS_FILE
STEPS=`cat ${LIST_NAME}`


