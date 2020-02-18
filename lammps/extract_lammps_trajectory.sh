#!/usr/bin/env bash

function usage
{
   echo "This script rewrites a LAMMPS trajectory. "
   echo "Usage:  extract_trajectory.sh -f TRAJ_FILE [-h]"
   echo "         -f TRAJ_FILE    LAMMPS trajectory file name"
   echo "         --start-step    initial step to add"
   echo "         --skip-first    skip first step"
   echo "         --last-step     last step to read"
   echo "         -h  --help      print this help"
   echo "Example:  extract_trajectory.sh -f water.lammpstrj --start-step 1000"
}

TRAJ_FILE=
VERBOSITY=1
START_STEP=0
SKIP_FIRST=0
LAST_STEP=-1

while [ $# -gt 0 ]; do
    case $1 in
        -f )             shift; TRAJ_FILE=$1
                         ;;
        -v )             VERBOSITY=0
                         ;;
        --start-step )   shift; START_STEP=$1
                         ;;
        --skip-first )   SKIP_FIRST=1
                         ;;
        --last-step )    shift; LAST_STEP=$1
                         ;;
        -h | --help )    usage
                         exit
                         ;;
        * )              usage
                         exit 1
    esac
    shift
done

if [[ ( (-z "$TRAJ_FILE") ) ]]; then
   usage
   exit 1
fi

echo "  Extracting trajectory:  $TRAJ_FILE" > "/dev/stderr"
awk -vVERB=${VERBOSITY} -vSTART_STEP=${START_STEP} -vSKIP_FIRST=${SKIP_FIRST} -vLAST_STEP=${LAST_STEP} '
BEGIN {
  step_idx = -1
  stepflag = 0    # 0 when reading headers and data, 1 when reading step
  currstep = -1   # current step
  if (LAST_STEP >= 0 )
    laststepflag = 1
  else
    laststepflag = 0
}
SKIP_FIRST == 1 && step_idx < 1 {
  if ($0 == "ITEM: TIMESTEP")
    step_idx++
  # do not print
}
step_idx >= 1 || SKIP_FIRST == 0 {
  if (stepflag == 0) {
    if ($0 == "ITEM: TIMESTEP") {
      step_idx++
      stepflag = 1
    }
    else
      print
  }
  else {    # read step
    curr_step = $1
    if (laststepflag && (curr_step > LAST_STEP))
      exit 0
    print "ITEM: TIMESTEP"
    print curr_step + START_STEP
    stepflag = 0
  }
}
END {
  printf("%d\n", curr_step) >"/dev/stderr"
  printf("%d steps read (%d - %d).\n", step_idx, START_STEP, curr_step + LAST_STEP) > "/dev/stderr"
}
' $TRAJ_FILE

