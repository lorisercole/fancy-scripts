import numpy as np
import sys


if (len(sys.argv) < 5):
     print "usage:\n  {} outfile step input1 ... inputN\n   please edit the source to modify the header of the data.\n".format(sys.argv[0])
     exit(-1)
step=int(sys.argv[2])
header="Step Time PotEng TotEng Lx Press Temp c_flusso[1] c_flusso[2] c_flusso[3] c_vcm_h2o[1][1] c_vcm_h2o[1][2] c_vcm_h2o[1][3] c_vcm_c2h5oh[1][1] c_vcm_c2h5oh[1][2] c_vcm_c2h5oh[1][3] ".strip()
n_data=len(header.split())


newbuf=[]
newbufts=[]

outfile=open(sys.argv[1],'w')
lastidx=0
idx_double_last=0

for f in sys.argv[3:]:
    oldbuf=newbuf
    oldbufts=newbufts
    with open(f,'r') as fp:
        print "reading file '{}'".format(f)
        newbuf=[]
        newbufts=[]
        data=False
        idx_double_line=[]
        for iline, line in enumerate(fp):
           if (not data) and line.strip()==header:
               data=True
               continue
           elif not data:
               print "line {} skipped".format(iline)
           if data:
               tmp=line.split()
               if (len(tmp)==n_data):
                   idx=int(tmp[0])
                   if (idx % step == 0):
                       try:
                           if lastidx >=idx:
                               if len(oldbufts) > idx_double_last+2 and oldbufts[idx_double_last+1]==idx:
                                   idx_double=idx_double_last+1
                               else:
                                   idx_double=oldbufts.index(idx)
                               idx_double_last=idx_double
                               idx_double_line.append([idx_double,len(newbuf)-1])
                               oldbuf[idx_double]=line
                           else:
                               raise ValueError
                       except ValueError:
                           newbuf.append(line)
                           newbufts.append(idx)
                           lastidx=idx
                   else:
                       print "timestep {} skipped.".format(tmp[0])
               else:
                   print "{} data lines read from file '{}'.".format(len(newbuf),f)
                   print "{} duplicates from previous data.".format(len(idx_double_line))
                   break
    #now write the old (that does not have the overwritten data)
    for line in oldbuf:
        outfile.write(line)
    print "{} lines written.\n".format(len(oldbuf))

for line in newbuf:
    outfile.write(line+'\n')
print "{} lines written.\n".format(len(newbuf))

