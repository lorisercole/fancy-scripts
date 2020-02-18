#!/usr/bin/env bash

function usage
{
   echo "This script extracts the current from a lammps log file. "
   echo "Usage:  extract_current.sh -f LOG_FILE [-h]"
   echo "         -f LOG_FILE LAMMPS log file name"
   echo "         -d DUMP_RUN label - used to identify the production run"
   echo "         -j          print only currents without Step/Time"
   echo "         -h  --help      print this help"
   echo "Example:  extract_current.sh -f water.log"
}

LOG_FILE=
DUMP_RUN='_dump_run'
VERBOSITY=1

while [ $# -gt 0 ]; do
    case $1 in
        -f )             shift; LOG_FILE=$1
                         ;;
        -d )             shift; DUMP_RUN=$1
                         ;;
        -j )             VERBOSITY=0
                         ;;
        -h | --help )    usage
                         exit
                         ;;
        * )              usage
                         exit 1
    esac
    shift
done

if [[ ( (-z "$LOG_FILE") ) ]]; then
   usage
   exit 1
fi

echo " DUMP RUN label:  "${DUMP_RUN} > "/dev/stderr"

awk -vDUMP=${DUMP_RUN} -vVERB=${VERBOSITY} '
BEGIN {
  flag = 0
  nfluxcol = 0
  stepcol = 0
  timecol = 0
  count = 0
}
($1 == "dump" || $1 == "#dump") && $2 == DUMP {
  ## production run found
  printf(" dump %s  found at line %d.\n", DUMP, NR) > "/dev/stderr"
  flag = 1
}
flag == 1 && $1 == "Step" {
  ## look for flux columns and start reading
  flag = 2
  for (i=1; i<=NF; i++) {
    if (($i ~ /^flux/) || ($i ~ /^c_flux/) || ($i ~ /^J/)) {
      nfluxcol++
      fluxcol[nfluxcol] = i
      printf("Found: %16s at line %d, column %d\n", $i, NR, i) > "/dev/stderr"
    }
    else if ($i == "Step") {
      stepcol = i
      printf("Found: %16s at line %d, column %d\n", $i, NR, i) > "/dev/stderr"
    }
    else if ($i == "Time") {
      timecol = i
      printf("Found: %16s at line %d, column %d\n", $i, NR, i) > "/dev/stderr"
    }
  }
  if (!stepcol && !timecol) {
    printf("Step or Time column not found!\n") > "/dev/stderr"
    exit
  }
}
flag == 2 {
  ## read data until Loop
  if ($1 == "Loop") {
    flag = 0
    exit
  }
  else {
    if (stepcol && VERB)
      printf("%s ", $stepcol)
    if (timecol && VERB)
      printf("%s ", $timecol)
    for (i=1; i<=nfluxcol; i++)
      printf(" %s", $fluxcol[i])
    printf("\n")
    count++
  }
}
END {
  if ( count == 0 )
    printf("ERROR: no steps found.\n") > "/dev/stderr"
  else
    printf("DONE:  %d steps * %d columns of flux data read.\n", count-1, nfluxcol) > "/dev/stderr"
}
' $LOG_FILE

