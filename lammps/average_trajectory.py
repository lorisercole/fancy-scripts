#!/usr/bin/python


import read_lammps_dump as rld

def average_trajectory(filename, autosave=None, autosave_freq=10000):
   """ average_trajectory(filename, PRESTORE_NSTEPS=1000)
     filename = LAMMPS Dump file """

   dump = rld.LAMMPS_Dump(filename, preload=False, group_vectors=False, GUI=False, quiet=True)

   #skeys = dump.all_ckeys.keys()[:]
   skeys = [x[0] for x in sorted(dump.all_ckeys.items(), key=lambda x: x[1])]  # sort all_ckeys
   skeys.remove('id')
   if 'type' in skeys:
      skeys.remove('type')
   if 'element' in skeys:
      skeys.remove('element')
   ave = {}
   for k in skeys:
      ave[k] = 0.0

   nstep = 0
   if autosave is None:
      try:
         while True:  # loop until EOF
            dump.read_timesteps(1, select_ckeys=skeys)  # read one time step
            nstep += 1
            for k in skeys:
               ave[k] = (float(nstep-1)/nstep)*ave[k] + (1.0/nstep)*dump.data[0][k]
            #print nstep
      except EOFError:
         print "Reached EOF."  # break
   else:
      try:
         while True:
            for i in xrange(autosave_freq):
               dump.read_timesteps(1, select_ckeys=skeys)  # read one time step
               nstep += 1
               for k in skeys:
                  ave[k] = (float(nstep-1)/nstep)*ave[k] + (1.0/nstep)*dump.data[0][k]
               #print nstep
            print "nstep = {:d} - Autosaving...".format(nstep)
            autosave(ave, skeys, nstep)
      except EOFError:
         print "Reached EOF."  # break
   print "  Average over {:d} steps.".format(nstep)
   return ave, skeys, nstep


def save_func(type, out_filename, in_filename):
   if (type == 'dump'):
      def w_dump(dic, skeys, nsteps):
         write_dump(out_filename, dic, skeys, in_filename, nsteps)
      return w_dump
   elif (type == 'table'):
      def w_table(dic, skeys, nsteps):
         write_table(out_filename, dic, skeys, nsteps)
      return w_table
   else:
      raise ValueError('Unvalid save type.')
   return


def write_dump(out_filename, dic, skeys, in_filename, nsteps):
   import numpy as np

   fin = open(in_filename, 'r')
   fout = open(out_filename, 'w')
   fout.write('# Average over {:d} steps\n'.format(nsteps))
   while True:  # copy the first part
      line = fin.readline()
      if 'ITEM: ATOMS' in line:
         break
      else:
         fout.write(line)
   fout.write("ITEM:ATOMS " + " ".join(skeys) + "\n")
   arr = np.transpose([ dic[k] for k in skeys ])[0]
   ids = np.transpose(np.ones((1,arr.shape[0]),dtype=int)*np.arange(arr.shape[0]))
   np.savetxt(fout, np.concatenate((ids, arr), axis=1), fmt='%d'+' %.18e'*len(skeys))
   fin.close()
   fout.close()
   print "  LAMMPS Dump file written:  ", out_filename
   return

def write_table(out_filename, dic, skeys, nsteps):
   import numpy as np

   fout = open(out_filename, 'w')
   fout.write('# Average over {:d} steps\n'.format(nsteps))
   fout.write("  ".join(skeys) + "\n")
   np.savetxt(fout, np.transpose([ dic[k] for k in skeys ])[0])
   fout.close()
   print "  Table file written:  ", out_filename
   return

################################################################################
def main ():
   """ This script reads a LAMMPS Dump file and returns the average atomic
   quantities (positions, velocities, ...).
   Example:
      python average_trajectory.py dump.lammpstrj -o average.lammpstrj -a 10000
   The -a option is used to save the temporary average every 10000 steps.
   """

   import argparse

   parser = argparse.ArgumentParser()
   parser.add_argument( 'lammpsdump_file', help='lammps dump file to read' )
   parser.add_argument( 'output_file', help='file where average will be saved (LAMMPS dump file format)' )
   parser.add_argument( '-t', '--table', action='store_true', help='save a table file instead of a LAMMPS dump' )
   parser.add_argument( '-a', '--autosave', type=int, help='autosave the average every this number of steps.')
   args = parser.parse_args()

   print type(args.autosave), args.autosave
   if args.table:
      save_type = 'table'
   else:
      save_type = 'dump'
   if args.autosave is None:
      ave, keys, nsteps = average_trajectory(args.lammpsdump_file)
   else:
      ave, keys, nsteps = average_trajectory(args.lammpsdump_file, save_func(save_type, args.output_file, args.lammpsdump_file), args.autosave)

   # save final results
   save_func(save_type, args.output_file, args.lammpsdump_file)(ave, keys, nsteps)
   #if args.table:
   #   write_table(args.output_file, ave, keys)
   #else:
   #   write_dump(args.output_file, ave, keys, args.lammpsdump_file)
   return 0

if __name__ == "__main__":
   main()

