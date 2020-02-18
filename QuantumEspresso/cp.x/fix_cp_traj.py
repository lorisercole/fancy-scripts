#!/usr/bin/python

#
# SCRIPT TO FIX cp.x TRAJECTORIES
#   it detects if a restart happened and deletes repeated steps
#   it also detects potential issues like missing steps
#

# not supported: CON, HRS, NCG, POL, SPR, STR, THE, WFC
# a check on the list of steps should be added

###############################################
import numpy as np
import os
from os import stat as fstat
from os.path import isfile
import argparse

def check_extra_steps(steps):
  # returns the indexes of the steps to be removed
  skip = []
  for t in xrange(len(steps)-1):
    if (steps[t] >= steps[t+1]):
      first = np.argmax(steps[:] == steps[t+1])
      print "  RESTART found at #{:d} step={:d} --> #{:d} step={:d} -- First occurance: #{:d} step={:d}  /-\-/-\-/-\  {:d} steps will be removed".format(t, int(steps[t]), t+1, int(steps[t+1]), first, int(steps[first]), t+1-first)
      skip.extend(range(first,t+1))
  return skip

def read_scalar_timeseries(filename):
  """Read a file of scalar/vector type:
  # step time Temp ...
  10  1.03  300.4 ...
  20  1.04  305.2 ...
  ..."""
  with open(filename, 'r') as f:
    line = f.readline()
    if (line.split()[0] == '#'):
       headline = line
    else:
       headline = []
  data = np.loadtxt(filename, dtype=str)
  steps = np.array(map(int, data[:,0]))
  return data, steps, headline

def read_matrix_timeseries(filename, nrows):
  """Read a file of matrix/atomic type:
  step time
  10.4356  -463.1021  67.10023
  -7.6432  -98.34529  343.3345
  ...(nrows lines per step)...
  step2 time2
  10.4356  -463.1021  67.10023
  -7.6432  -98.34529  343.3345
  ...(nrows lines per step)...
"""
  steps = []
  times = []
  data = []
  with open(filename, 'r') as f:
    while True:
      line = f.readline().split()
      if (len(line) == 0):  # EOF
        print "  END OF FILE"
        break
      if (len(line) == 2):    # new step line
        steps.append(int(line[0]))
        times.append(line[1])
      else:
        raise RuntimeError('ERROR. Wrong number of atoms or incomplete step.\n STEP={}\n line={}'.format(steps[-1],line))
      data_t = ['']*nrows
      for i in xrange(nrows):
        line = f.readline().split()
        data_t[i] = line
      data.append(np.array(data_t))
  return np.array(data), np.array(steps), np.array(times)

def read_matrix_key_timeseries(filename, step_key='STEP:', ncomment_lines=1):
  """Read a file of matrix/atomic type with a step-KEY and comment lines.
  KEY  10  0.10
  comment comment comment ...
  -20.39  -20.11  -19.97  -19.89  -19.87
  -19.87  -19.82  -19.78  -19.72  -19.68
  ...
  KEY  20  0.20
  comment comment comment ...
  -20.39  -20.11  -19.97  -19.89  -19.87
  -19.87  -19.82  -19.78  -19.72  -19.68
  ...
"""
  with open(filename, 'r') as f:
    i = -1
    while True:
      line = f.readline().split()
      if (len(line) == 0):  # EOF
        raise RuntimeError('ERROR. step_key not found.')
      if (line[0] == step_key):
        if (i == -1):
          i = 0
        else:
          break
      elif (i >= 0):
        i += 1
  nrows = i - ncomment_lines
  print "  nrows = ", nrows
  
  steps = []
  times = []
  comment = []
  data = []
  with open(filename, 'r') as f:
    while True:
      line = f.readline().split()
      if (len(line) == 0):  # EOF
        print "  END OF FILE"
        break
      if (line[0] == step_key):   # new step line
        steps.append(int(line[1]))
        times.append(line[2])
      elif (len(line) == 2) and (step_key in line[0]):  # if there is no space between step_key and step
        steps.append(int(line[0].replace(step_key, '')))
        times.append(line[1])
      else:
        raise RuntimeError('ERROR. Wrong number of comment lines?\n STEP={}\n line={}'.format(steps[-1],line))
      comm_t = ['']*ncomment_lines
      for i in xrange(ncomment_lines):
        line = f.readline()
        comm_t[i] = line
      comment.append(np.array(comm_t))
      data_t = ['']*nrows
      for i in xrange(nrows):
        line = f.readline()
        data_t[i] = line
      data.append(data_t)
  return data, np.array(steps), np.array(times), np.array(comment)

def check_steps(steps):
  ##  check that all steps are consistent
  first = steps[0]
  delta = steps[1] - first
  last  = steps[-1]
  print '  Steps (start,end,delta): ({:}, {:}, {:})'.format(first,last,delta)
  if ((last-first)%delta != 0):
    print '!!! Warning: inconsistent step delta ({})'.format(delta)
  nsteps_expected = int((last-first)/delta) + 1
  nsteps = len(steps)
  print '  There are {:6d} steps'.format(nsteps)
  if (nsteps_expected != nsteps):
    print '!!!  There should be {:6d} steps'.format(nsteps_expected)

  ## check all steps, for safety
  missing = []
  for t in np.arange(first, last+delta, delta):
    if t not in steps:
      missing.append(t)
  if (len(missing) > 0):
    print '!!! Warning: some steps are missing:'
    for t in missing:
      print '  ', t
  else:
    print '  OK'
  return

#################################################

def main ():
  """This program reads the outputs of a CP-QE simulation and fixes the timeseries from restarts that may have happened.
  Example:
    python fix_cp_traj.py silica silicaok

  Supported files:     .cel .eig .evp .for .nos .pos .str .vel
  Not (yet) supported: .con .hrs .ncg .pol .spr .the .wfc
  """
  _epilog = """---
  Code written by Loris Ercole.
  SISSA, Via Bonomea, 265 - 34136 Trieste ITALY
  """
  parser = argparse.ArgumentParser()
  parser = argparse.ArgumentParser(description=main.__doc__, epilog=_epilog, formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('prefix', type=str, help='prefix of the files in the QE output directory.')
  parser.add_argument('outprefix', type=str, help='new prefix of the files to be written.')
  parser.add_argument('-n', '--natoms', type=int, required=True, help='number of atoms')
  args = parser.parse_args()
  prefix = args.prefix
  outprefix = args.outprefix
  if (prefix == outprefix):
    raise ValueError('For your data safety, input and output prefix should differ!')
    return 1
  natoms = args.natoms

  # CEL - box cell file
  filename = prefix + '.cel'
  print "\n* Fixing {} file...".format(filename)
  outfilename = outprefix + '.cel'
  if os.path.isfile(filename) and fstat(filename).st_size:  # if file is not empty
    try:
      data, steps, times = read_matrix_timeseries(filename, 3)
      skip = check_extra_steps(steps)
      data = np.delete(data, skip, 0)
      steps = np.delete(steps, skip, 0)
      check_steps(steps)
      times = np.delete(times, skip, 0)
      with open(outfilename, 'w') as f:
        for s, t, d in zip(steps, times, data):
          f.write(str(s) + ' ' + t + '\n')
          np.savetxt(f, d, fmt=' %s')
      print "  --> {} written".format(outfilename)
    except RuntimeError as e:
      print 'Error reading file.\n{}'.format(e)
  else:
    print "  {} is empty.".format(filename)
  
  # EIG - eigenvalues file
  filename = prefix + '.eig'
  print "\n* Fixing {} file...".format(filename)
  outfilename = outprefix + '.eig'
  if os.path.isfile(filename) and fstat(filename).st_size:  # if file is not empty
    try:
      data, steps, times, comment = read_matrix_key_timeseries(filename, 'STEP:', 1)
      skip = check_extra_steps(steps)
      data = np.delete(data, skip, 0)
      steps = np.delete(steps, skip, 0)
      times = np.delete(times, skip, 0)
      check_steps(steps)
      comment = np.delete(comment, skip, 0)
      with open(outfilename, 'w') as f:
        for s, t, c, d in zip(steps, times, comment, data):
          f.write('  STEP:  ' + str(s) + ' ' + t + '\n')
          f.write(c)
          for dd in d:
            f.write(dd)
      print "  --> {} written".format(outfilename)
    except RuntimeError as e:
      print 'Error reading file.\n{}'.format(e)
  else:
    print "  {} is empty.".format(filename)
  
  # EVP - thermo file
  filename = prefix + '.evp'
  print "\n* Fixing {} file...".format(filename)
  outfilename = outprefix + '.evp'
  if os.path.isfile(filename) and fstat(filename).st_size:  # if file is not empty
    try:
      data, steps, headline = read_scalar_timeseries(filename)
      skip = check_extra_steps(steps)
      data = np.delete(data, skip, 0)
      steps = np.delete(steps, skip, 0)
      check_steps(steps)
      with open(outfilename, 'w') as f:
        if len(headline):
          f.write(headline)
        np.savetxt(f, data, fmt=' %s')
      print "  --> {} written".format(outfilename)
    except RuntimeError as e:
      print 'Error reading file.\n{}'.format(e)
  else:
    print "  {} is empty.".format(filename)
  
  # FOR - forces file
  filename = prefix + '.for'
  print "\n* Fixing {} file...".format(filename)
  outfilename = outprefix + '.for'
  if os.path.isfile(filename) and fstat(filename).st_size:  # if file is not empty
    try:
      data, steps, times = read_matrix_timeseries(filename, natoms)
      skip = check_extra_steps(steps)
      data = np.delete(data, skip, 0)
      steps = np.delete(steps, skip, 0)
      times = np.delete(times, skip, 0)
      check_steps(steps)
      with open(outfilename, 'w') as f:
        for s, t, d in zip(steps, times, data):
          f.write(str(s) + ' ' + t + '\n')
          np.savetxt(f, d, fmt=' %s')
      print "  --> {} written".format(outfilename)
    except RuntimeError as e:
      print 'Error reading file.\n{}'.format(e)
  else:
    print "  {} is empty.".format(filename)
  
  # NOS - nos file
  filename = prefix + '.nos'
  print "\n* Fixing {} file...".format(filename)
  outfilename = outprefix + '.nos'
  if os.path.isfile(filename) and fstat(filename).st_size:  # if file is not empty
    try:
      data, steps, headline = read_scalar_timeseries(filename)
      skip = check_extra_steps(steps)
      data = np.delete(data, skip, 0)
      steps = np.delete(steps, skip, 0)
      check_steps(steps)
      with open(outfilename, 'w') as f:
        if len(headline):
          f.write(headline)
        np.savetxt(f, data, fmt=' %s')
      print "  --> {} written".format(outfilename)
    except RuntimeError as e:
      print 'Error reading file.\n{}'.format(e)
  else:
    print "  {} is empty.".format(filename)
  
  # POS - positions file
  filename = prefix + '.pos'
  print "\n* Fixing {} file...".format(filename)
  outfilename = outprefix + '.pos'
  if os.path.isfile(filename) and fstat(filename).st_size:  # if file is not empty
    try:
      data, steps, times = read_matrix_timeseries(filename, natoms)
      skip = check_extra_steps(steps)
      data = np.delete(data, skip, 0)
      steps = np.delete(steps, skip, 0)
      times = np.delete(times, skip, 0)
      check_steps(steps)
      with open(outfilename, 'w') as f:
        for s, t, d in zip(steps, times, data):
          f.write(str(s) + ' ' + t + '\n')
          np.savetxt(f, d, fmt=' %s')
      print "  --> {} written".format(outfilename)
    except RuntimeError as e:
      print 'Error reading file.\n{}'.format(e)
  else:
    print "  {} is empty.".format(filename)
  
  # STR - box stress tensor file
  filename = prefix + '.str'
  print "\n* Fixing {} file...".format(filename)
  outfilename = outprefix + '.str'
  if os.path.isfile(filename) and fstat(filename).st_size:  # if file is not empty
    try:
      data, steps, times = read_matrix_timeseries(filename, 3)
      skip = check_extra_steps(steps)
      data = np.delete(data, skip, 0)
      steps = np.delete(steps, skip, 0)
      times = np.delete(times, skip, 0)
      check_steps(steps)
      with open(outfilename, 'w') as f:
        for s, t, d in zip(steps, times, data):
          f.write(str(s) + ' ' + t + '\n')
          np.savetxt(f, d, fmt=' %s')
      print "  --> {} written".format(outfilename)
    except RuntimeError as e:
      print 'Error reading file.\n{}'.format(e)
  else:
    print "  {} is empty.".format(filename)
  
  # VEL - velocities file
  filename = prefix + '.vel'
  print "\n* Fixing {} file...".format(filename)
  outfilename = outprefix + '.vel'
  if os.path.isfile(filename) and fstat(filename).st_size:  # if file is not empty
    try:
      data, steps, times = read_matrix_timeseries(filename, natoms)
      skip = check_extra_steps(steps)
      data = np.delete(data, skip, 0)
      steps = np.delete(steps, skip, 0)
      times = np.delete(times, skip, 0)
      check_steps(steps)
      with open(outfilename, 'w') as f:
        for s, t, d in zip(steps, times, data):
          f.write(str(s) + ' ' + t + '\n')
          np.savetxt(f, d, fmt=' %s')
      print "  --> {} written".format(outfilename)
    except RuntimeError as e:
      print 'Error reading file.\n{}'.format(e)
  else:
    print "  {} is empty.".format(filename)

  return 0

if __name__ == "__main__":
  main()
