#!/usr/bin/env bash

function usage {
   echo -e "
This program computes the average lattice constant of a NPT calculation.
  Usage:  ./compute_density.sh FILE
     FILE = Lammps data file" > /dev/stderr
}

FILE=$1

if [[ -z "$FILE" ]]; then
   usage
   echo "File Error"
   exit 1
fi

awk '
$3 == "xlo" {
  dx = $2-$1
}
$3 == "ylo" {
  dy = $2-$1
}
$3 == "zlo" {
  dz = $2-$1
}

(massflag == 1) && (NF == 2) {
  ntypes++
  m[$1] = $2
}
(atomsflag == 1) && (NF > 2){
  n[$2]++
  natoms++
}

$1 == "Masses" {
  massflag = 1
  atomsflag = 0
  next
}
$1 == "Atoms" {
  massflag = 0
  if ($3 == "charge")
    atomsflag = 1
  else {
    print "not supported" > "/dev/stderr"
    exit
  }
  next
}
$1 == "Velocities" {
  massflag = 0
  atomsflag = 0
  next
}
NF == 1 {
  print "Unrecognized field" > "/dev/stderr"
}
END {
  totmass = 0
  for (i=1; i<=ntypes; i++)
    totmass += n[i]*m[i]
  volume = dx*dy*dz
  ndens = natoms/volume   # number density
  mdens = totmass/volume/6.02214129*10.
  printf("MDENSITY  %18.15e g/cm^3\n", mdens)
  printf("NDENSITY  %18.15e atoms/A^3\n", ndens)
  printf("VOLUME    %18.15e A^3\n", volume)
  printf("NATOMS    %d\n", natoms)
  printf("NTYPES    %d\n", ntypes)
  for (i=1; i<=ntypes; i++)
    printf("%2d : %12.9f * %4d\n", i, m[i], n[i])
}' $FILE


