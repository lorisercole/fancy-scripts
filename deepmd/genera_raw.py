#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#import multiprocessing as mp
#import time
#
#def foo_pool(x):
#    time.sleep(2)
#    return x*x
#
#result_list = []
#def log_result(result):
#    # This is called whenever foo_pool(i) returns a result.
#    # result_list is modified only by the main process, not the pool workers.
#    result_list.append(result)
#
#def apply_async_with_callback():
#    pool = mp.Pool()
#    for i in range(10):
#        pool.apply_async(foo_pool, args = (i, ), callback = log_result)
#    pool.close()
#    pool.join()
#    print(result_list)
#
#if __name__ == '__main__':
#    apply_async_with_callback()


import numpy as np

Ha=27.2114 #eV
rBohr=0.529772 #Ang
KcalMol=0.0433641153 #eV
eV=1.60217662 #10^-19 J
bar=1.0e-6/eV #eV/Ang^3

def read_matrix(file):
    matrix=np.zeros( (3,3) )
    for idim in range(3):
        line=file.readline()
        matrix[idim,:]=np.array(line.split(),dtype='float64')
    return matrix

def read_lammps_trajectory(dumpfile,natoms, SnapShots,readVirial = True):
    """read lammps dumpfile with header (not saved)"""

    File = open(dumpfile,'r')

    data={}
    data['pos']=np.zeros((SnapShots,natoms,3))
    data['for']=np.zeros((SnapShots,natoms,3))
    data['vir']=np.zeros((SnapShots,natoms,3,3))
    data['cel']=np.zeros((SnapShots,3,3))
    data['ts']=np.zeros((SnapShots))
    data['typ']=np.zeros((natoms))

    t = 0
    while (t < SnapShots):
        #read header
        h1 = File.readline()
        time = File.readline()
        data['ts'][t]=int(time)
        h2 = File.readline()
        numatoms = File.readline()
        h3 = File.readline()
        xlen = np.array(File.readline().split(),dtype=np.double)
        ylen = np.array(File.readline().split(),dtype=np.double)
        zlen = np.array(File.readline().split(),dtype=np.double)
        h4 = File.readline()
        data['cel'][t,:,:]=np.array([[xlen[1]-xlen[0],0,0],[0,ylen[1]-ylen[0],0],[0,0,zlen[1]-zlen[0]]])
        for a in range(natoms):
            #Read string -> strip '\n' char -> split into new list
            lines = File.readline()
            line=lines.split()
            data_line=np.array(line,dtype=np.double)
            iatom=int(round(data_line[0]))-1
            data['for'][t,iatom,:]=data_line[9:12]*KcalMol
            data['pos'][t,iatom,:]=data_line[3:6]
            if (readVirial):
                data['vir'][t,iatom,0,0]=data_line[12]*bar
                data['vir'][t,iatom,1,1]=data_line[13]*bar
                data['vir'][t,iatom,2,2]=data_line[14]*bar
                data['vir'][t,iatom,0,1]=data_line[15]*bar
                data['vir'][t,iatom,0,2]=data_line[16]*bar
                data['vir'][t,iatom,1,2]=data_line[17]*bar
                data['vir'][t,iatom,2,1]=data['vir'][t,iatom,1,2]
                data['vir'][t,iatom,2,0]=data['vir'][t,iatom,0,2]
                data['vir'][t,iatom,1,0]=data['vir'][t,iatom,0,1]
           
            if t==0:
                 data['typ'][iatom]=data_line[2]
            else:
                if data_line[2] != data['typ'][iatom]:
                     raise RuntimeError('Atom types cannot change! (atom {})'.format(iatom))
        t += 1

    File.close()
    return data

def read_energy_tot_virial(logfile,data,skip,start):
    nstep=data['ts'].shape[0]
    data_line=np.loadtxt(logfile,usecols=(0,2,10,11,12,13,14,15))

    data['Tvir']=np.zeros((nstep,3,3))
    data['e'] = np.zeros((nstep))

    for istep in range(data['ts'].shape[0]):
        if int(round(data['ts'][istep])) != int(round(data_line[istep*skip+start,0])):
            raise RuntimeError('Timesteps {} {} does not match!'.format(data['ts'][istep],int(round(data_line[istep*skip+start,0]))))
        data['e'][istep]=data_line[istep*skip+start,1]*KcalMol
        data['Tvir'][istep,0,0]=-data_line[istep*skip+start,2]*bar
        data['Tvir'][istep,1,1]=-data_line[istep*skip+start,3]*bar
        data['Tvir'][istep,2,2]=-data_line[istep*skip+start,4]*bar
        data['Tvir'][istep,0,1]=-data_line[istep*skip+start,5]*bar
        data['Tvir'][istep,0,2]=-data_line[istep*skip+start,6]*bar
        data['Tvir'][istep,1,2]=-data_line[istep*skip+start,7]*bar
        data['Tvir'][istep,2,1]=data['Tvir'][istep,1,2]
        data['Tvir'][istep,2,0]=data['Tvir'][istep,0,2]
        data['Tvir'][istep,1,0]=data['Tvir'][istep,0,1]

def read_file_pos_for_evp_cel(namepos,namefor,nameevp,namecel,nstep,natoms,shuffle=False):
    """name* : file di output prodotti da cp.x di quantum espressso
       nstep : numero di passi da leggere dai file (che devono essere allineati!)
       natoms : numero di atomi

       MESCOLA I TIMESTEP IN MODO CASUALE se shuffle == True (utile per generare dati di input per il train di una rete neurale)

       assume le unità di output di cp.x (hartree e raggi di bohr), e converte in eV e angstrom (e unità derivate da queste per le forze)
    """        
    data={} 
    data['pos']=np.zeros((nstep,natoms,3))
    data['for']=np.zeros((nstep,natoms,3))
    data['cel']=np.zeros((nstep,3,3))
    data['evp']=np.zeros((nstep,11))
    filepos=open(namepos)
    filefor=open(namefor)
    fileevp=open(nameevp)
    filecel=open(namecel)
    headerevp=fileevp.readline()
    s=np.arange(nstep,dtype='int')
    if (shuffle):
        np.random.shuffle(s)
    for ostep in range(nstep):
        istep=s[ostep]
        if (ostep%10==0):
            print ostep,' ' ,
        #lettura posizioni
        linepos = filepos.readline()
#        print linepos
        if len(linepos) == 0:  # EOF
            raise RuntimeError("End Of file")
        natoms_r=np.fromstring(linepos,dtype='float64',sep=' ')
        if natoms_r.size != 2:
            print linepos, "-", natoms_r,natoms_r.size
            raise RuntimeError("Different number of atoms in step {} ({},{})".format(istep,natoms,natoms_r))


        #lettura forze
        linefor = filefor.readline()
#        print linepos
        if len(linefor) == 0:  # EOF
            raise RuntimeError("End Of file")
        natoms_r=np.fromstring(linepos,dtype='float64',sep=' ')
        if natoms_r.size != 2:
            print linefor, "-", natoms_r,natoms_r.size
            raise RuntimeError("Different number of atoms in step {} ({},{})".format(istep,natoms,natoms_r))

        #lettura cella
        linecel = filecel.readline()
#        print linepos
        if len(linecel) == 0:  # EOF
            raise RuntimeError("End Of file")
        natoms_r=np.fromstring(linecel,dtype='float64',sep=' ')
        if natoms_r.size != 2:
            print linecel, "-", natoms_r,natoms_r.size
            raise RuntimeError("Different number of atoms in step {} ({},{})".format(istep,natoms,natoms_r))

	#lettura file evp
        lineevp=fileevp.readline()
        levp=np.fromstring(lineevp,dtype='float64',sep=' ')
        data['evp'][istep,:]=levp
#        print levp        


	if linefor != linepos:
            raise RuntimeError("Different timesteps between force and position files!")
	if linefor != linecel:
            raise RuntimeError("Different timesteps between force and cell files!")
        if natoms_r[0]!=levp[0] or abs(1-natoms_r[1]/levp[1])>0.001:
            print natoms_r[0],levp[0],'{:6.4e}'.format(natoms_r[1]) , '{:6.4e}'.format(levp[1])
            raise RuntimeError("Different timesteps between cell and evp files!")
      
	data['cel'][istep,:,:]=read_matrix(filecel)
                      
       
        for iatom in range(natoms):
            linepos = filepos.readline()
            linefor = filefor.readline()

#            print iatom,linepos
            values = np.array(linepos.split())#,dtype='S2, 'float64', 'float64', 'float64'')
            data['pos'][istep,iatom,:]=values
       
            values = np.array(linefor.split())#,dtype='S2, 'float64', 'float64', 'float64'')
            data['for'][istep,iatom,:]=values
       
    
    data['pos']=data['pos']*rBohr
    data['cel']=data['cel']*rBohr
    data['for']=data['for']*(Ha/rBohr)
    data['evp'][:,2]=data['evp'][:,2]*Ha
    data['evp'][:,5]=data['evp'][:,5]*Ha
    data['evp'][:,6]=data['evp'][:,6]*Ha
    data['evp'][:,7]=data['evp'][:,7]*Ha
    data['evp'][:,8]=data['evp'][:,8]*Ha
       
    return data


def read_multifile_pos_for_evp_cel(namespos,namesfor,namesevp,namescel,nsteps,natoms,shuffle):
    totdata={}
    totdata['pos']=np.zeros((np.sum(nsteps),natoms,3))
    totdata['for']=np.zeros((np.sum(nsteps),natoms,3))
    totdata['cel']=np.zeros((np.sum(nsteps),3,3))
    totdata['evp']=np.zeros((np.sum(nsteps),11))
    s=np.arange(np.sum(nsteps),dtype='int')
    if (shuffle):
        np.random.shuffle(s)

    idx_s=0
    for namepos,namefor,nameevp,namecel,nstep in zip(namespos,namesfor,namesevp,namescel,nsteps):
        data = read_file_pos_for_evp_cel(namepos,namefor,nameevp,namecel,nstep,natoms,shuffle=False)
        #shuffle data
        for istep in range(nstep):
            totdata['pos'][s[idx_s+istep],:,:]=data['pos'][istep,:,:]
            totdata['for'][s[idx_s+istep],:,:]=data['for'][istep,:,:]
            totdata['cel'][s[idx_s+istep],:,:]=data['cel'][istep,:,:]
            totdata['evp'][s[idx_s+istep],:]=data['evp'][istep,:]
        idx_s=idx_s+nstep

    return totdata
        
def read_multiple_folder_prefix(prefixes, suffix,nsteps,natoms,shuffle):
    namespos=[]
    namesfor=[]
    namesevp=[]
    namescel=[]
    for prefix in prefixes:
        namespos.append('{}/{}.pos'.format(prefix,suffix))
        namesfor.append('{}/{}.for'.format(prefix,suffix))
        namesevp.append('{}/{}.evp'.format(prefix,suffix))
        namescel.append('{}/{}.cel'.format(prefix,suffix))
    return read_multifile_pos_for_evp_cel(namespos,namesfor,namesevp,namescel,nsteps,natoms,shuffle)

def write_xyz(nameout,data):
    o=open(nameout,'w')
    for istep in range(data['pos'].shape[0]):
        o.write('{}\n{}\n'.format(data['pos'].shape[1],istep))
        for iatom in range(data['pos'].shape[1]):
             t='2'
	     if iatom<data['pos'].shape[1]/2:
                 t='1'
             o.write('{} {} {} {}\n'.format(t,data['pos'][istep,iatom,0],data['pos'][istep,iatom,1],data['pos'][istep,iatom,2]))


def write_raw3(nameout,data,key):
    o=open(nameout,'w')
    print key,  data[key].shape
    for istep in range(data[key].shape[0]):
        for iatom in range(data[key].shape[1]):
            o.write('{} {} {} '.format(data[key][istep,iatom,0],data[key][istep,iatom,1],data[key][istep,iatom,2]))
        o.write('\n')

def write_raw1(nameout,data,key):
    o=open(nameout,'w')
    print key,  data[key].shape
    for istep in range(data[key].shape[0]):
        o.write('{} \n'.format(data[key][istep]))

def write_raw0(nameout,data,key):
    o=open(nameout,'w')
    print key,  data[key].shape
    for istep in range(data[key].shape[0]):
        o.write('{} '.format(data[key][istep]))
    o.write('\n')

def write_raw_energy(nameout,data):
    key='evp'
    o=open(nameout,'w')
    for istep in range(data[key].shape[0]):
        o.write('{} \n'.format(data[key][istep,5]))

def write_type_H2O(nameout,natoms):
    o=open(nameout,'w')
    for iatom in range(natoms):
         if (iatom<64):
             o.write('0 ')
         else:
             o.write('1 ')

def write_type_SiO2(nameout,natoms):
    o=open(nameout,'w')
    for iatom in range(natoms):
         if (iatom<64):
             o.write('0 ')
         else:
             o.write('1 ')

def write_data_lammps(nameout,data,istep,):
    o=open(nameout,'w')
    o.write('''LAMMPS Description
     {}  atoms
     0  bonds
     0  angles
     0  dihedrals
     0  impropers

     2  atom types

  0 {} xlo xhi
  0 {} ylo yhi
  0 {} zlo zhi

Masses  

        1  28.0855
        2  15.9994

Atoms # atomic

'''.format(data['pos'].shape[1],data['cel'][istep,0,0],data['cel'][istep,1,1],data['cel'][istep,2,2]))
    for iatom in range(data['pos'].shape[1]):
        typeatom=2
        if iatom <144:
            typeatom=1
        o.write('{} {} {} {} {}\n'.format(iatom+1,typeatom,data['pos'][istep,iatom,0],data['pos'][istep,iatom,1],data['pos'][istep,iatom,2]))

prefix='raw.mu50/'

#dat=read_file_pos_for_evp_cel(prefix+'silica.pos',prefix+'silica.for',prefix+'silica.evp',prefix+'silica.cel',19520,432)


10088
10132
29775


dat=read_multiple_folder_prefix(['360.mu50','380.mu50','400.mu50'],'tmp/water',(10087,10131,29774),192,True)
write_raw3(prefix+'coord.raw',dat,'pos')
write_raw3(prefix+'force.raw',dat,'for')
write_raw3(prefix+'box.raw',dat,'cel')
write_raw_energy(prefix+'energy.raw',dat)
write_type_SiO2(prefix+'type.raw',192)
#write_data_lammps('frame.data',dat,19000)

