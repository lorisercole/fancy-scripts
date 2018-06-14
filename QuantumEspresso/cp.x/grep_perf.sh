#!/bin/bash

function usage
{
  echo 'usage:'
  echo '  ./grep_perf.sh "various_outputs_cp.x_names*" | sort -k 7 -n'
  echo
  echo '     outputs a sorted (by wall time of a cp step) list of parallelization'
  echo '     parameters and wall time of one cp step'
  echo '     (useful to do some benchmarks)'
  echo '     Note that all the files name must be in the first argument, so " " are needed'
}

if [ $# -eq 0 ]; then
    usage
    exit 1
fi

echo "#MPI_PROCS OMP_THREADS BANDS_GROUPS TASK_GROUPS ORTHO  InitTime 1StepTime  file MAIN_LOOP_CALLS"

for f in $1 
do
    MPI_PROC=$(grep "Number of MPI"  $f | awk '{print $5}')
    if [ -z "$MPI_PROCS" ]; then
      MPI_PROC=$(grep "Parallel version (MPI), running on" $f | awk '{print $6}')
    fi
    OMP_THREADS=$(grep "Threads/MPI"  $f | awk '{print $3}')
    if [ -z "$OMP_THREADS" ]; then
      OMP_THREADS=0
    fi
    BAND_GROUPS=$(grep "band groups division"  $f | awk '{print $6}')
    if [ -z "$BAND_GROUPS" ]; then
      BAND_GROUPS=0
    fi
    TASK_GROUPS=$(grep "wavefunctions fft division"  $f | awk '{print $8}')
    if [ -z "$TASK_GROUPS" ]; then
      TASK_GROUPS=0
    fi
    ORTHO=$(grep "ortho sub-group" $f | awk '{print $5}')
    if [ -z "$ORTHO" ]; then
      ORTHO=0
    fi
    INIT_TIME=$(grep "initialize" $f | awk '{print $5}')
    MAIN_LOOP=$(grep "main_loop" $f | awk '{print $5}')
    MAIN_LOOP_CALLS=$(grep "main_loop" $f | awk '{print $8}')
    if [ -z "$MAIN_LOOP" ]; then
      ONE_STEP_TIME='NaN'
      INIT_TIME='NaN'
      echo " * $f  file not complete." > '/dev/stderr'
      continue
    else
      ONE_STEP_TIME=`awk -vtot=${MAIN_LOOP%s} -vcalls=$MAIN_LOOP_CALLS 'BEGIN{printf("%.3f", tot/calls)}'`
    fi
    ff=${f#silica_SCF.70.}
    echo $MPI_PROC $OMP_THREADS $BAND_GROUPS $TASK_GROUPS $ORTHO  ${INIT_TIME%s} $ONE_STEP_TIME ${ff%.out} $MAIN_LOOP_CALLS
done

