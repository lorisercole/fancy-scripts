#!/usr/bin/env bash

echo -e "
This program computes the average lattice constant of a NPT calculation.
  Usage:  ./average_latconst.sh FILE TBEGIN
     FILE = Lammps log file
     TBEGIN = Initial step to average" > /dev/stderr

FILE=$1
TBEGIN=$2

if [[ -z "$FILE" ]]; then
   echo "Error"
   exit 1
fi

awk -vTBEGIN=$TBEGIN '
  BEGIN {
    lxid = 0
    pid = 0
    volid = 0
    t = 0
    lx = 0.
    vol = 0.
    p = 0.
  }
  $1 == "Step" {
    for (i=1; i<=NF; i++) {
      if ($i == "Lx") {
        lxid = i
      }
      if ($i == "Press") {
        pid = i
      }
      if ($i == "Volume") {
        volid = i
      }
    }
    next
  }
  $1 == "Loop" {
    lxid = 0
    volid = 0
  }
  ((lxid != 0) || (volid != 0)) && ($1 >= TBEGIN) {
    t++
    if (lxid)
      lx += $lxid
    if (pid)
      p += $pid
    if (volid)
      vol += $volid
  }

  END {
    printf "Average over %d steps...\n", t  >> "/dev/stderr"
    if (pid)
      printf "Average Pressure    =   %.20g\n", p/t  >> "/dev/stderr"
    if (volid)
      printf "Average Volume      =   %.20g\n", vol/t  >> "/dev/stderr"
    printf "Average lx          =   %.20g\n", lx/t  >> "/dev/stderr"
    printf "%.20g", lx/t
  }
' $FILE

