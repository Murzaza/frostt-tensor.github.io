#!/usr/bin/env python3

import sys
import gzip
import argparse
from datetime import datetime
from functools import reduce

##############################################################################
#
# CONSTANTS
#

# Where the hosted files will be found.
DB_URL = 'http://www-users.cs.umn.edu/~shaden/frostt_data'

VERSION_STR = '0.1'

PROG_NAME = 'build_tensor.py'

PROG_DESC='Construct a markdown file for a tensor to be used by FROSTT.'
##############################################################################


##############################################################################
#
# Argument parsing
#

parser = argparse.ArgumentParser(prog=PROG_NAME, description=PROG_DESC)
parser.add_argument('--version', action='version',
    version='{} v{}'.format(PROG_NAME, VERSION_STR))
parser.add_argument('-t', '--tensor', help='tensor file to extract stats (.tns, .tns,gz)', type=str)
parser.add_argument('-o', '--output', help='output file', type=str)
parser.add_argument('--title', help='tensor title', type=str)
parser.add_argument('-c', '--cite', help='file with bibtex entry', type=str)
parser.add_argument('-n', '--nnz', help='number of non-zeros', default=0, type=int)
parser.add_argument('--desc', help='description file', type=str)
parser.add_argument('-f', '--files', help='file containing tensor files', type=str)
parser.add_argument('-d', '--dims', help='comma-separated list of dimensions',
    type=str)
parser.add_argument('--tags', help='comma-separated list of tags', type=str)

env = parser.parse_args()
##############################################################################



##############################################################################
#
# File parsing
#

def open_file(fname):
  if fname.endswith('gz'):
    return gzip.open(fname, 'rb')
  else:
    return open(fname, 'r')

def get_nnz(fin):
  for line in fin:
    if type(line) == bytes:
      line = line.decode('utf-8')
    if line[0] == '#':
      continue
    yield line.strip().split()
##############################################################################



##############################################################################
#
# Tensor info
#

description = ''
if env.desc:
  with open(env.desc, 'r') as desc_file:
    description = desc_file.read()
    # ensure text is indented
    description = description.replace('\n','\n  ')

citation = ''
if env.cite:
  with open(env.cite, 'r') as cite_file:
    citation = cite_file.read()
    # ensure text is indented
    citation = citation.replace('\n','\n  ')


nonzeros = env.nnz
order = 0
dims = []
if env.dims:
  dims = [int(x) for x in env.dims.split(',')]
  order = len(dims)

files = []
with open(env.files, 'r') as fin:
  for line in fin:
    line = line.split()
    location = '{}/{}'.format(DB_URL, line[0])
    rest = ' '.join(line[1:])
    files.append((location, rest))

tags = env.tags.split(',')
##############################################################################


# Parse data from tensor file if necessary
if env.tensor and ((nonzeros == 0) or (order == 0) or (dims == [])):
  with open_file(env.tensor) as fin:
    for nnz_list in get_nnz(fin):
      order = len(nnz_list) - 1
      nonzeros += 1

      # store dims if necessary
      if not env.dims:
        if not dims:
          dims = [0] * order
        for m in range(order):
          dims[m] = max(dims[m], int(nnz_list[m]))


# determine output file
if env.output is None:
  env.output = 'output.md'
  if env.tensor:
    env.tensor.replace('.tns', '.md')
    if env.tensor.endswith('.gz'):
      env.output = env.output[:-3]




# write markdown file
with open(env.output, 'w') as fout:
  print('---', file=fout)
  if env.title:
    print('title: {}\n'.format(env.title), file=fout)
  else:
    print('title: {}\n'.format(env.output.replace('.md', '')), file=fout)

  print('description: >\n  {}\n'.format(description), file=fout)

  print("order: '{}'".format(order), file=fout)
  print("nnz: '{:,d}'".format(nonzeros), file=fout)

  dim_str= ['{:,d}'.format(d) for d in dims]
  print('dims: {}'.format(dim_str[:order]), file=fout)

  density = float(nonzeros) / reduce(lambda x, y: float(x) * float(y), dims)
  print("density: '{:0.3e}'".format(density), file=fout)

  print('files:', file=fout)
  for f in files:
    print(' - ["{}", {}]'.format(f[0], f[1]), file=fout)
  print('\n', file=fout)

  print('citation: >\n  {}\n'.format(citation), file=fout)
  print('tags: [{}]'.format(', '.join(tags)), file=fout)
  today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  print('\n# generated on ({}) by {} v{}'
      .format(today, PROG_NAME, VERSION_STR), file=fout)
  print('---', file=fout)

