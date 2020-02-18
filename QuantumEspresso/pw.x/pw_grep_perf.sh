#!/bin/bash

function usage
{
  echo 'usage:'
  echo '  ./pw_grep_perf.sh "various_outputs_cp.x_names*" | sort -k 5 -n'
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

#echo "#MPI_PROCS OMP_THREADS BANDS_GROUPS TASK_GROUPS ORTHO  InitTime 1StepTime  file"
echo "#MPI_PROCS BANDS_GROUPS TASK_GROUPS ORTHO  Time PWSCFwall file"

for f in $1 
do
    MPI_PROC=$(grep "Parallel version "  $f | awk '{for (i=1;i<=NF;i++) if ($i=="on") print $(i+1)}')
#    OMP_THREADS=$(grep "Threads/MPI"  $f | awk '{print $3}')
    BAND_GROUPS=$(grep "band groups division"  $f | awk '{print $6}')
    if [ -z "$BAND_GROUPS" ]; then
      BAND_GROUPS=1
    fi
    TASK_GROUPS=$(grep "wavefunctions fft division"  $f | awk '{print $8}')
    if [ -z "$TASK_GROUPS" ]; then
      TASK_GROUPS=1
    fi
    ORTHO=$(grep "distributed-memory algorithm" $f | awk '{print $8}')
    INIT_TIME=$(grep "init_run     :" $f | awk '{print $5}')
    ELECTRONS=$(grep "electrons    :" $f | awk '{print $5}')
    FORCES=$(grep "forces       :" $f | awk '{print $5}')
    PWSCF=$(grep "PWSCF        :" $f | awk '{for (i=1;i<=NF;i++){if ($i=="CPU") cpu=i;} for (i=1;i<=NF;i++){if ($i=="WALL") wall=i;} if (wall==cpu+2) print $(wall-1); else print $(wall-2),$(wall-1)}')
    if [ -z "$INIT_TIME" ]; then
      INIT_TIME='NaN'
      ELECTRONS='NaN'
      FORCES='NaN'
      echo " * $f  file not complete." > '/dev/stderr'
      continue
    else
      TIME=`awk -vt1=${INIT_TIME%s} -vt2=${ELECTRONS%s} -vt3={FORCES%s} 'BEGIN{printf("%.3f", t1+t2+t3)}'`
    fi
    #ff=${f#silica_SCF.70.}
    echo $MPI_PROC $BAND_GROUPS $TASK_GROUPS $ORTHO  ${TIME} ${PWSCF}  $f
    #echo $MPI_PROC $OMP_THREADS $BAND_GROUPS $TASK_GROUPS $ORTHO  ${INIT_TIME%s} $ONE_STEP_TIME  ${ff%.out}
done

