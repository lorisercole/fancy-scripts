#!/usr/bin/env bash

function usage
{
   echo "This script rescales the simulation box (cubic boxes only, charge style only)./"
   echo "Usage:  rescale_cell.sh -f FILE -r CELLSIZE [-c] [-h]"
   echo "         -f FILE         LAMMPS data file name"
   echo "         -r CELLSIZE     new cell size in any direction"
   echo "         -c              center the new box on the origin"
   echo "         -xyz            save an additional xyz file"
   echo "         -h  --help      print this help"
   echo "Example:  rescale_cell.sh -f silica.init -r 10.5 -c > silica2.init"
}

FILE=
CSZ=
CENTER=0
XYZ=0

while [ $# -gt 0 ]; do
    case $1 in
        -f )             shift; FILE=$1
                         ;;
        -r )             shift; CSZ=$1
                         ;;
        -c )             shift; CENTER=1
                         ;;
        -xyz )           shift; XYZ=1
                         ;;
        -h | --help )    usage
                         exit
                         ;;
        * )              usage
                         exit 1
    esac
    shift
done

if [[ ( (-z "$FILE")||(-z "$CSZ") ) ]]; then
   usage
   exit 1
fi

# check if file exist
if [ ! -e ${FILE} ]
then
        printf "\n\tFile does not exists!\n\n"                                          > /dev/stderr
        exit 1
else
        printf "\n\tInput file: ${FILE}\n\n"                                            > /dev/stderr
fi


awk -vCSZ=$CSZ -vCENTER=$CENTER -vXYZ=$XYZ -vXYZFILE=${FILE}_rep.xyz '
BEGIN{
   xlo = 0
   xhi = 0
   ylo = 0
   yhi = 0
   zlo = 0
   zhi = 0
   atomflag = 0
   NATOMS = 0
}
$1 == "ITEM:" {
   printf("! Invalid file format. This is not a LAMMPS data file. Dump files are not supported.\n") > "/dev/stderr"
   exit
}
$2 == "atoms" {
   NATOMS = $1
   printf("%d atoms\n", NATOMS)
   printf("NUMBER OF ATOMS:\n  %d atoms\n", NATOMS) > "/dev/stderr"
   next
}
$3 == "xlo" {
   xlo = $1
   xhi = $2
   xlength = xhi-xlo
   newxcenter = xlo+0.5*xlength
   rsc_factor = CSZ / xlength
   printf("RESCALING FACTOR = %20.18lf\n", rsc_factor) > "/dev/stderr"
   if (CENTER)
      printf("CENTERED\n") > "/dev/stderr"
   printf("original: %13.11lf %13.11lf xlo xhi   xlength = %13.11lf\n", xlo, xhi, xlength) > "/dev/stderr"
   if (CENTER) {
      printf("%.16e %.16e xlo xhi\n", -CSZ*0.5, CSZ*0.5)  #centered
      printf("new:      %13.11lf %13.11lf xlo xhi   xlength = %13.11lf\n", -CSZ*0.5, CSZ*0.5, CSZ) > "/dev/stderr"
   }
   else {
      printf("%.16e %.16e xlo xhi\n", xlo, xlo+CSZ)
      printf("new:      %13.11lf %13.11lf xlo xhi   xlength = %13.11lf\n", xlo, xlo+CSZ, CSZ) > "/dev/stderr"
   }
   next
}
$3 == "ylo" {
   ylo = $1
   yhi = $2
   ylength = yhi-ylo
   newycenter = ylo+0.5*ylength
   printf("original: %13.11lf %13.11lf ylo yhi\n", ylo, yhi) > "/dev/stderr"
   if (CENTER) {
      printf("%.16e %.16e ylo yhi\n", -CSZ*0.5, CSZ*0.5)  #centered
      printf("new:      %13.11lf %13.11lf ylo yhi   xlength = %13.11lf\n", -CSZ*0.5, CSZ*0.5, CSZ) > "/dev/stderr"
   }
   else {
      printf("%.16e %.16e ylo yhi\n", ylo, ylo+CSZ)
      printf("new:      %13.11lf %13.11lf ylo yhi   xlength = %13.11lf\n", ylo, ylo+CSZ, CSZ) > "/dev/stderr"
   }
   next
}
$3 == "zlo" {
   zlo = $1
   zhi = $2
   zlength = zhi-zlo
   newzcenter = zlo+0.5*zlength
   printf("original: %13.11lf %13.11lf zlo zhi\n", zlo, zhi) > "/dev/stderr"
   if (CENTER) {
      printf("%.16e %.16e zlo zhi\n", -CSZ*0.5, CSZ*0.5)  #centered
      printf("new:      %13.11lf %13.11lf zlo zhi   xlength = %13.11lf\n", -CSZ*0.5, CSZ*0.5, CSZ) > "/dev/stderr"
   }
   else {
      printf("%.16e %.16e zlo zhi\n", zlo, zlo+CSZ)
      printf("new:      %13.11lf %13.11lf zlo zhi   xlength = %13.11lf\n", zlo, zlo+CSZ, CSZ) > "/dev/stderr"
   }
   next
}
$0 == "Atoms # charge" {
   atomflag = 2
   print $0
   next
}
$0 == "Velocities" {
   exit
}
atomflag == 2 {
   print
   atomflag--
   next
}
atomflag == 1 && $1 ~ /^[0-9]+$/ {
   if ( NF >= 6 && NATOMS > 0) {
      idx = $1
      atom_type[idx] = $2
      atom_q[idx] = $3
      atom_x[idx] = $4
      atom_y[idx] = $5
      atom_z[idx] = $6
   }
   else {
      print "???"
   }
}
atomflag == 0 {
   print
}
atomflag == 1 && $1 !~ /^[0-9]+$/ {
   exit
}
END {
   for (idx = 1; idx <= NATOMS; idx++) {
      if (CENTER)  # center box
         printf( "%d %d %9.7lf %.16e %.16e %.16e\n", idx, atom_type[idx], atom_q[idx], 
                     (atom_x[idx]-newxcenter)*rsc_factor, (atom_y[idx]-newycenter)*rsc_factor, (atom_z[idx]-newzcenter)*rsc_factor )
      else
         printf( "%d %d %9.7lf %.16e %.16e %.16e\n", idx, atom_type[idx], atom_q[idx],
                     (atom_x[idx]-xlo)*rsc_factor+xlo, (atom_y[idx]-ylo)*rsc_factor+ylo, (atom_z[idx]-zlo)*rsc_factor+zlo )
   }

   if ( XYZ == 1 ) {
      print NATOMS  > XYZFILE
      print
      for (idx = 1; idx <= NATOMS; idx++) {
         if ( atom_type[idx] == 1 )  atype = "Si";
         if ( atom_type[idx] == 2 )  atype = "O";
         if (CENTER)  # center box
            print atype, (atom_x[idx]-newxcenter)*rsc_factor, (atom_y[idx]-newycenter)*rsc_factor, (atom_z[idx]-newzcenter)*rsc_factor  >> XYZFILE
         else
            print atype, (atom_x[idx]-xlo)*rsc_factor+xlo, (atom_y[idx]-ylo)*rsc_factor+ylo, (atom_z[idx]-zlo)*rsc_factor+zlo  >> XYZFILE
      }
   }
}
' $FILE

exit 0

