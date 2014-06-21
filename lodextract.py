#!/usr/bin/python

import zlib, os
import struct

import Image, ImageDraw
import StringIO

lod = open("H3bitmap.lod")
lod.seek(8)
files_count = struct.unpack("i", lod.read(4))[0]
files=[]
for file in range(32,33):
    lod.seek(92+(file*32))
    name = lod.read(16).split("\0")[0]
    offset = struct.unpack("i", lod.read(4))[0] #offset
    size_orig = struct.unpack("i", lod.read(4))[0] #size_original
    type = struct.unpack("i", lod.read(4))[0] #type
    size_comp = struct.unpack("i", lod.read(4))[0] #size_compressed

    lod.seek(offset)

    if size_comp:
        pcx = zlib.decompress(lod.read(size_comp))
    else:
        pcx = lod.read(size_orig)

    if type == 16:
        size = struct.unpack("i", pcx[:4])[0]
        width = struct.unpack("i", pcx[4:8])[0]
        height = struct.unpack("I", pcx[8:12])[0]
        print size, width, height
	im = Image.fromstring("L", (width, height), pcx[12:12+size])
	im.putpalette(pcx[12+size:12+size+768])
        im.save(' '.join([str(file),name]), "PNG")
    if type == 17:
        size = struct.unpack("i", pcx[:4])[0]
        width = struct.unpack("i", pcx[4:8])[0]
        height = struct.unpack("I", pcx[8:12])[0]
        print size, width, height
	im = Image.fromstring("RGB", (width, height), pcx[12:12+size])
        im.save(' '.join([str(file),name]), "PNG")
    elif type in (1, 2, 64, 65, 66, 67, 68, 69, 70, 71, 73, 79, 80, 96):
        print file, name
        file = open(' '.join([str(file),name]), "w")
        file.write(pcx)
        file.close()
    else:
        print i, name, type
        sys.exit("not supported %d"%type)

lod.close()
