#!/usr/bin/python

import zlib, os
import struct

import Image, ImageDraw

lod = open("H3bitmap.lod")
lod.seek(8)
files_count = struct.unpack("i", lod.read(4))[0]
files=[]
for file in range(2745,2793):
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
        print file, name, width, height

        im = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(im)
        bla=[]
        for i in range(256):
            bla.append((ord(pcx[12+size+i*3]),ord(pcx[12+size+i*3+1]),ord(pcx[12+size+i*3+2])))

        for i in range(size):
            a =ord(pcx[12+i])
            if bla[a] == (0,255,255):
                draw.point((i-int(i/width)*width,int(i/width)), fill=(0,0,0,0))
            else:
                draw.point((i-int(i/width)*width,int(i/width)), fill=bla[a])
        im.save(' '.join([str(file),name]), "PNG")
    elif type == 17:
        size = struct.unpack("i", pcx[:4])[0]
        width = struct.unpack("i", pcx[4:8])[0]
        height = struct.unpack("I", pcx[8:12])[0]
        print file, name, width, height

        im = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(im)

        for i in range(size/3):
            if ord(pcx[12+i*3]) == 0 and ord(pcx[13+i*3]) == 255 and ord(pcx[14+i*3]) == 255:
                draw.point((i-int(i/width)*width,int(i/width)), fill=(0,0,0,0))
            else:
                draw.point((i-int(i/width)*width,int(i/width)), fill=(ord(pcx[12+i*3]),ord(pcx[13+i*3]),ord(pcx[14+i*3])))
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
