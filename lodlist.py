#!/usr/bin/python

import struct
from sys import argv

lod = open(argv[1])
lod.seek(8)
files_count = struct.unpack("i", lod.read(4))[0]
files=[]
for file in xrange(files_count):
    lod.seek(92+(file*32))
    name = lod.read(16).split("\0")[0]
    offset = struct.unpack("i", lod.read(4))[0] #offset
    size_orig = struct.unpack("i", lod.read(4))[0] #size_original
    type = struct.unpack("i", lod.read(4))[0] #type
    size_comp = struct.unpack("i", lod.read(4))[0] #size_compressed
    print name

lod.close()
