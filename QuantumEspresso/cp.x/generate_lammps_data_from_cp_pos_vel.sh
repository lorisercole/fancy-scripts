#!/bin/bash
#set -x

if [[ -z $5 ]]
then
	echo "usage: $0 [output cp .pos] [typefile] [NATOMS] [NFRAME] [outfile]"
        echo 'typefile is a file with the type of each atom on each line (1 or 2)'
        echo "default is 2 atom types and m1=15.9994 uma and m2=1.008 uma (modify the script otherwise)"
        echo 
        echo "later you can use the [outfile] in lammps with the command:
read_data [outfile]"
        exit -1
fi

NAT=$3
NFRAME=$4
ALAT=$( head -n $(( 4*NFRAME)) ${1%.pos}.cel | tail -n 1 | awk '{print $3*.529177}' )
echo "alat = $ALAT"
echo "timestep $( head -n $(( 4*NFRAME)) ${1%.pos}.cel | tail -n 4 | head -n 1)"

cat > $5 << EOF
LAMMPS Description      
                        
     $NAT  atoms         
     0  bonds           
     0  angles          
     0  dihedrals       
     0  impropers       
                        
                        
     2  atom types      
                        
 0 $ALAT xlo xhi
 0 $ALAT ylo yhi
 0 $ALAT zlo zhi
                        
Masses                  
                        
        1       15.9994 
        2       1.008   
                        
Atoms                   
                        
EOF
paste <( seq 1 $NAT) $2 <( head -n $(( (NAT+1)*NFRAME)) $1 | tail -n $NAT | awk '{print $1*.529177,$2*.529177,$3*.529177}') >> $5

cat >> $5 << EOF

Velocities

EOF
paste <( seq 1 $NAT)  <( head -n $(( (NAT+1)*NFRAME)) ${1%.pos}.vel | tail -n $NAT | awk '{print $1*.529177/2.4189e-5,$2*.529177/2.4189e-5,$3*.529177/2.4189e-5}') >> $5
