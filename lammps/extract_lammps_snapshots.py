#!/usr/bin/python

import numpy as np
import argparse


def main():
   """This program extracts the desired snapshots from a lammps dump file trajectory. It can convert the units from LAMMPS metal to QE-CP units.
   NOTICE: atom id are not sorted"""

   BOHR = 0.52917720859    # Bohr constant in Angstrom
   TAU  = 0.5*4.837768652311145e-5  # tau_CP constant in ps

   parser = argparse.ArgumentParser()
   parser.add_argument( 'inputfile', help='lammps dump file to read' )
   parser.add_argument( '-s', '--steps', nargs='*', dest='step', help='list of time steps to extract', type=int )
   parser.add_argument( '-o', '--out', help='output file. Default: inputfile_STEP.extension' )
   parser.add_argument( '-c', '--convert', action='store_true', help='convert units from LAMMPS metal to CP' )
   parser.add_argument( '-cr', '--convert_real', action='store_true', help='convert units from LAMMPS real to CP' )
   parser.add_argument( '-CP', action='store_true', help='convert units from LAMMPS real to CP.x input (correction for buggy velocities included)' )
   parser.add_argument( '-t', '--atomtypenames', nargs='*', dest='atomtypenames', help='list of atom type names', type=str )
   args = parser.parse_args()

   inputfile = args.inputfile
   outputfile = args.out
   steps = args.step
   convert_units = args.convert
   convert_units_real = args.convert_real
   CP_OUTPUT = args.CP
   atomtypenames = args.atomtypenames

   if ( outputfile == None ):
      if '.' in inputfile:   # inputfile has extension
         outputfile = inputfile[:inputfile.rindex('.')]
      else:
         outputfile = inputfile

   if ( steps == None or len(steps) == 0 ):
      print '! no steps given.'
      return 1

   # sort and check steps
   steps.sort()
   if ( steps[0] < 0 ):
      print '! steps should be positive integer numbers.'
      return 1


   print ' Input file: ', inputfile
   print ' Extracting steps: ', steps

   # open input/output files
   f = open( inputfile, 'r' )


   # extract snapshots
   line = f.readline()
   while line:
      if not line.find('ITEM: TIMESTEP\n'):   # if TIMESTEP found
         line = f.readline()
         current_STEP = int(line)

         # analyze current_STEP if it is in the list
         if current_STEP in steps:

            # variables to read
            lammpsvaridx = { 
               'type': None,
               'x':   None, 
               'y':   None,
               'z':   None,
               'vx':   None,
               'vy':   None,
               'vz':   None
            }
            lammpsvar = { 
               'type': None,
               'x':   None, 
               'y':   None,
               'z':   None,
               'vx':   None,
               'vy':   None,
               'vz':   None
            }
            print "current_STEP =", current_STEP

            # loop until NUMBER OF ATOMS is found
            while f.readline().find('ITEM: NUMBER OF ATOMS\n'):
               pass
            current_NATOMS = int(f.readline())
            print "current_NATOMS", current_NATOMS

            # loop until BOX BOUNDS is found
            line = f.readline()
            while line.find('ITEM: BOX BOUNDS'):
               line = f.readline()
            line = f.readline().split()
            box_x = float(line[1]) - float(line[0])
            box_x0 = float(line[0])
            line = f.readline().split()
            box_y = float(line[1]) - float(line[0])
            line = f.readline().split()
            box_z = float(line[1]) - float(line[0])
            if (box_y != box_x):
               raise Warning('Only cubic boxes are supported!')
            if (box_z != box_x):
               raise Warning('Only cubic boxes are supported!')

            # loop until ATOMS id is found
            line = f.readline()
            while line.find('ITEM: ATOMS id'):
               line = f.readline()

            # then analyze header
            line = line.split()
            for key in lammpsvaridx.iterkeys():
               try:
                  lammpsvaridx[key] = line.index(key)-2   # save column number corresponding to key
               except ValueError:
                  print '!!', key, 'variable not found in file.'
                  return 1
            print "IDX: ", lammpsvaridx
            # initialize data structure
            for key in lammpsvar.iterkeys():
               lammpsvar[key] = [0.]*current_NATOMS

            # start reading data
            for i in range(current_NATOMS):
               line = f.readline().split()
               for key in lammpsvaridx.iterkeys():
                  lammpsvar[key][i] = line[ lammpsvaridx[key] ]

            # convert data to numbers
            for key,value in lammpsvar.iteritems():
               if ( key != 'type' ):
                  lammpsvar[key] = np.array( map( float, value ) )
               else:
                  lammpsvar[key] = np.array( map( int, value ) )

            # define set of non-identical types
            attypes = set( lammpsvar['type'] )
            print "TYPES: ", attypes
            print "NAMES: ", atomtypenames


            # write output
            if CP_OUTPUT:
              # use CP input style output
              if atomtypenames is None:
                 raise ValueError('You must provide atom type names.')
              if (len(atomtypenames) != len(attypes)):
                 raise ValueError('Number of atom type names do not match the number of atom types found. Check your input.')
              fout = open(outputfile + '_cp.in', 'w')
              fout.write( '! STEP = {:d} - NATOMS = {:d} -'.format(current_STEP, current_NATOMS) )
              for itype, attype in enumerate(attypes):
                 fout.write( ' #{:d}-{}({:d})'.format(attype, atomtypenames[itype], np.sum(lammpsvar['type']==attype)) )
              fout.write('\n &SYSTEM\n' +
                         '    ibrav = 1,\n' +
                         '    celldm(1) = {:f},\n'.format(box_x/BOHR) +  # box size (a.u.)
                         '    nat = {:d},\n'.format(current_NATOMS) +
                         '    ntyp = {:d},\n'.format(len(attypes)) +
                         '/\n')  # NOTICE: only CUBIC boxes supported
              fout.write('\nATOMIC_POSITIONS {crystal}\n')
              for itype, attype in enumerate(attypes):
                 pos = np.vstack(( lammpsvar['x'][lammpsvar['type']==attype],\
                                   lammpsvar['y'][lammpsvar['type']==attype],\
                                   lammpsvar['z'][lammpsvar['type']==attype] )).T
                 pos = (pos - box_x0) / box_x  # scale coordinates
                 for atpos in pos:
                    fout.write('{:2} {:.15f} {:.15f} {:.15f}\n'.format(atomtypenames[itype], atpos[0], atpos[1], atpos[2]) )

              fout.write('\n\nATOMIC_VELOCITIES { a.u }\n')
              for itype, attype in enumerate(attypes):
                 vel = np.vstack(( lammpsvar['vx'][lammpsvar['type']==attype],\
                                   lammpsvar['vy'][lammpsvar['type']==attype],\
                                   lammpsvar['vz'][lammpsvar['type']==attype] )).T
                 if convert_units_real:
                   vel *= TAU/BOHR/1000./(box_x/BOHR)  # division by alat (a.u.)to correct CP.x error
                 else:
                   vel *= TAU/BOHR/(box_x/BOHR)  # division by alat (a.u.) to correct CP.x error
                 for atvel in vel:
                    fout.write('{:2} {:.12e} {:.12e} {:.12e}\n'.format(atomtypenames[itype], atvel[0], atvel[1], atvel[2]) )
              fout.write('\n')
              fout.close()

            else:
              # write data to .pos and .vel files
              print "STEP: ", current_STEP
              if convert_units:
                fout_pos = open(outputfile + '_step_' + str(current_STEP) + '.pos', 'w')
                fout_vel = open(outputfile + '_step_' + str(current_STEP) + '.vel', 'w')
              else:
                fout_pos = open(outputfile + '_step_' + str(current_STEP) + '.pos_Ang', 'w')
                fout_vel = open(outputfile + '_step_' + str(current_STEP) + '.vel_Ang_ps', 'w')
              fout_pos.write( str(current_NATOMS) )
              fout_vel.write( str(current_NATOMS) )
              for attype in attypes:
                 fout_pos.write( ' #' + str(attype) + '(' + str((lammpsvar['type']==attype).sum()) + ')' )
                 fout_vel.write( ' #' + str(attype) + '(' + str((lammpsvar['type']==attype).sum()) + ')' )
              fout_pos.write( '\n' )
              fout_vel.write( '\n' )
              for attype in attypes:
                 pos = np.vstack(( lammpsvar['x'][lammpsvar['type']==attype], lammpsvar['y'][lammpsvar['type']==attype], lammpsvar['z'][lammpsvar['type']==attype] ))
                 vel = np.vstack(( lammpsvar['vx'][lammpsvar['type']==attype], lammpsvar['vy'][lammpsvar['type']==attype], lammpsvar['vz'][lammpsvar['type']==attype] ))
                 if convert_units:
                   np.savetxt( fout_pos, pos.T/BOHR )
                   if convert_units_real:
                     np.savetxt( fout_vel, vel.T/BOHR*TAU/1000. )
                   else:
                     np.savetxt( fout_vel, vel.T/BOHR*TAU )
                 else:
                   np.savetxt( fout_pos, pos.T )
                   np.savetxt( fout_vel, vel.T )
              fout_pos.close()
              fout_vel.close()

            # delete this step from the list and check if there are others to analyze
            del steps[0]
            if ( len(steps) == 0 ):
               break

         else:      # current STEP not to be analyzed
            pass

      else:
         pass

      # keep reading until another TIMESTEP starts
      line = f.readline()

   # end of file (unless break before)
   if ( len(steps) != 0 ):
      print 'These time steps have not been found: ', steps, len(steps)
   #print 'last line:', line

   return 0

if __name__ == "__main__":
   main()
