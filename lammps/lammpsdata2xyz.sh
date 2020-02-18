#!/usr/bin/env bash

if [ $# -ne 1 ]; then
  echo "This script converts a LAMMPS data file to a xyz file"
  echo "Usage: ./lammpsdata2xyz.sh DATAFILENAME > XYZFILE"
  exit 1
fi

FILE=$1
#FOUT=${FILE%*.init}.xyz

awk -vFOUT=${FOUT} '
BEGIN {
  read_atoms = 0
}
(NF == 2) && ($2 == "atoms") {
  NAT = $1

  printf "%d\nConverted from %s\n", NAT, FILENAME
  next
}
(NF == 3) && ($2 == "atom") && ($3 == "types") {
  NTYPE = $1
  next
}
($1 == "Atoms") {
  if ($3 == "atomic") {
    col_id = 1
    col_type = 2
    col_x = 3
    col_y = 4
    col_z = 5
  }
  else if ($3 == "charge") {
    col_id = 1
    col_type = 2
    col_q = 3
    col_x = 4
    col_y = 5
    col_z = 6
  }
  else {
    print "Atoms type not supported."
  }
  read_atoms = 1
  next
}
(read_atoms == 1) && (NF > 0) {
  if (!($1 ~ /^[0-9]+$/)) {   # if not numeric
    read_atoms = 0
    next
  }
  else {
    print $col_type, $col_x, $col_y, $col_z
  }
}
' $FILE

