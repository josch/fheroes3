#!/usr/bin/python
"""
    homm3lodextract - extract data from heroes of might and magic 3 lod
                      archives and convert pcx images and def animations to png
                      images
    
    copyright 2008  - Johannes 'josch' Schauer <j.schauer@email.de>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import zlib, os
import struct
import sys

import Image, ImageDraw

def read_frame_3(width, height, data):
    length = height*width/32 #length of scanline
    #UNSIGNED short here!!
    offsets = struct.unpack("%dH"%length, data[:length*2])
    offsets += (len(data),)
    
    raw = ""
    for i in xrange(len(offsets)-1):
        line = data[offsets[i]:offsets[i+1]]
        pos = 0
        while pos < len(line):
            count = ord(line[pos])
            if 0x00 <= count <= 0x1F: #empty
                raw += '\x00'*(count+1)
                pos +=1
            elif 0x20 <= count <= 0x3F: #light shadow
                raw += '\x01'*(count-31)
                pos +=1
            elif 0x40 <= count <= 0x5F: #only used in Tshre.def and AvGnoll.def
                raw += '\x02'*(count-63)
                pos +=1
            elif 0x60 <= count <= 0x7F: #only used in Tshre.def
                raw += '\x03'*(count-95)
                pos +=1
            elif 0x80 <= count <= 0x9F: #strong shadow
                raw += '\x04'*(count-127)
                pos +=1
            elif 0xA0 <= count <= 0xBF: #replaced by player color
                raw += '\x05'*(count-159)
                pos +=1
            elif 0xE0 <= count <= 0xFF: #normal colors
                raw += line[pos+1:pos+count-222]
                pos += count-222
            else:
                raise Exception("%02X"%count)
    return raw

def read_frame_1(width, height, data):
    try:
        offsets = struct.unpack("%di"%height, data[:height*4])
    except:
        #this failes for SGTWMTB.def
        print "cannot read scanline offses"
        return None
    offsets += (len(data),)
    
    raw = ""
    for i in xrange(len(offsets)-1):
        line = data[offsets[i]:offsets[i+1]]
        pos = 0
        while pos < len(line):
            try:
                count = ord(line[pos+1])+1
            except IndexError:
                #this failes for SGTWMTA.def, SGTWMTB.def
                print "cannot read scanline"
                return None
            if ord(line[pos]) is 0xFF:
                raw+=line[pos+2:pos+2+count]
                pos+=2+count
            else:
                raw+=line[pos]*count
                pos+=2
    return raw

def save_frame(path, num, data, palette, width, height, fname):
    (data_size, frame_type, fwidth, fheight, img_width, img_height, offset_x,
        offset_y) = struct.unpack("8i", data[0:32])
    
    #this only does not match in OVSLOT.def
    if width != fwidth:
        print "frame width %d does not match def width %d"%(fwidth, width)
    if height != fheight:
        print "frame height %d does not match def height %d"%(fheight, height)
    data = data[32:32+data_size]
    
    if frame_type is 0:
        #type 0 is raw indexed image data
        buffer = data
    elif frame_type is 1:
        buffer = read_frame_1(img_width, img_height, data)
    elif frame_type is 2:
        #this is seldomly used and seems to decode fine using type3
        buffer = read_frame_3(img_width, img_height, data)
    elif frame_type is 3:
        buffer = read_frame_3(img_width, img_height, data)
    else:
        raise Exception("frame type %d not supported"%frame_type)
    
    if buffer is not None:
        im = Image.new("P", (fwidth, fheight), 0x00)
        im.paste(
            Image.frombuffer(
                'RGB',
                (img_width, img_height),
                buffer,
                'raw', 'P', 0, 1),
            (offset_x, offset_y))
        
        if fname == "clrrvr.def":
            path = os.path.join(path, "%d"%num)
            if not os.path.exists(path):
                os.makedirs(path)
            for i in xrange(12):
                im.putpalette(palette[:189*3]
                         +palette[201*3-i*3:201*3]
                         +palette[189*3:201*3-i*3]
                         +palette[201*3:])
                im2 = im.convert("RGBA")
                data = im2.load()
                for x in xrange(im.size[0]):
                    for y in xrange(im.size[1]):
                        if data[x, y] == (0, 255, 255, 255):
                            data[x, y] = (0, 0, 0, 0)
                if os.path.exists(os.path.join(path, "%d.png"%i)):
                    print "overwriting %s" % os.path.join(path, "%d.png"%i)
                im2.save(os.path.join(path, "%d.png"%i), "PNG")
        elif fname == "lavrvr.def":
            path = os.path.join(path, "%d"%num)
            if not os.path.exists(path):
                os.makedirs(path)
            for i in xrange(9):
                im.putpalette(palette[:240*3]
                         +palette[249*3-i*3:249*3]
                         +palette[240*3:249*3-i*3]
                         +palette[249*3:])
                im2 = im.convert("RGBA")
                data = im2.load()
                for x in xrange(im.size[0]):
                    for y in xrange(im.size[1]):
                        if data[x, y] == (0, 255, 255, 255):
                            data[x, y] = (0, 0, 0, 0)
                if os.path.exists(os.path.join(path, "%d.png"%i)):
                    print "overwriting %s" % os.path.join(path, "%d.png"%i)
                im2.save(os.path.join(path, "%d.png"%i), "PNG")
        elif fname == "mudrvr.def":
            path = os.path.join(path, "%d"%num)
            if not os.path.exists(path):
                os.makedirs(path)
            for i in xrange(12):
                im.putpalette(palette[:228*3]
                         +palette[240*3-i*3:240*3]
                         +palette[228*3:240*3-i*3]
                         +palette[240*3:])
                im2 = im.convert("RGBA")
                data = im2.load()
                for x in xrange(im.size[0]):
                    for y in xrange(im.size[1]):
                        if data[x, y] == (0, 255, 255, 255):
                            data[x, y] = (0, 0, 0, 0)
                if os.path.exists(os.path.join(path, "%d.png"%i)):
                    print "overwriting %s" % os.path.join(path, "%d.png"%i)
                im2.save(os.path.join(path, "%d.png"%i), "PNG")
        elif fname == "watrtl.def":
            path = os.path.join(path, "%d"%num)
            if not os.path.exists(path):
                os.makedirs(path)
            for i in xrange(12):
                im.putpalette(palette[:229*3]
                         +palette[241*3-i*3:241*3]
                         +palette[229*3:241*3-i*3]
                         +palette[241*3:242*3]
                         +palette[254*3-i*3:254*3]
                         +palette[242*3:254*3-i*3]
                         +palette[254*3:])
                if os.path.exists(os.path.join(path, "%d.png"%i)):
                    print "overwriting %s" % os.path.join(path, "%d.png"%i)
                im.convert("RGBA").save(os.path.join(path, "%d.png"%i), "PNG")
        else:
            im.putpalette(palette)
            im = im.convert("RGBA")
            data = im.load()
            for x in xrange(im.size[0]):
                for y in xrange(im.size[1]):
                    if data[x, y] == (0, 255, 255, 255):
                        data[x, y] = (0, 0, 0, 0)
                    elif data[x, y] == (255, 150, 255, 255):
                        data[x, y] = (0, 0, 0, 64)
                    elif data[x, y] == (255, 151, 255, 255):
                        data[x, y] = (0, 0, 0, 64)
                    elif data[x, y] == (255, 0, 255, 255):
                        data[x, y] = (0, 0, 0, 128)
            if os.path.exists(os.path.join(path, "%d.png"%num)):
                print "overwriting %s" % os.path.join(path, "%d.png"%num)
            im.save(os.path.join(path, "%d.png"%num), "PNG")
    else:
        print "invalid frame"

def save_file(fid, name, ftype, data):
    if not os.path.exists(os.path.join("data", ftype)):
        os.makedirs(os.path.join("data", ftype))
    if os.path.exists(os.path.join("data", ftype, name)):
        print "overwriting %s" % os.path.join("data", ftype, name)
    file = open(os.path.join("data", ftype, name), "w")
    file.write(data)
    file.close()

def lod_extract(filename):
    lod = open(filename)
    if lod.read(4) != "LOD\x00":
        raise Exception("not an LOD archive")
    (version, files_count) = struct.unpack("2i", lod.read(8))
    print "Version: %d, File Count: %d"%(version, files_count) #RoE: 200, AB: 500

    for fid in xrange(files_count):
        lod.seek(92+(fid*32))
        name = lod.read(16).split('\x00')[0].lower()
        (offset, size_orig, ftype, size_comp) = \
            struct.unpack("4i", lod.read(16))
        lod.seek(offset)
        
        if size_comp:
            pcx = zlib.decompress(lod.read(size_comp))
        else:
            pcx = lod.read(size_orig)
        
        if ftype == 1: #h3c file
            print fid, name, ftype
            save_file(fid, name, "campaigns", pcx)
        elif ftype == 2: #txt file
            print fid, name, ftype
            save_file(fid, name, "txt", pcx)
        elif ftype == 16: #pcx palette image
            (size, width, height) = struct.unpack("3i", pcx[:12])
            print fid, name, width, height

            if not os.path.exists(os.path.join("data", "pcx_palette")):
                os.makedirs(os.path.join("data", "pcx_palette"))
                
            im = Image.frombuffer('RGB', (width, height), pcx[12:size+12],
                'raw', 'P', 0, 1)
            im.putpalette(pcx[12+size:12+size+3*256])
            if os.path.exists(os.path.join("data", "pcx_palette", name)):
                print "overwriting %s" % os.path.join("data", "pcx_palette", name)
            im.save(os.path.join("data", "pcx_palette", name), "PNG")
        elif ftype == 17: #pcx rgb image
            (size, width, height) = struct.unpack("3i", pcx[:12])
            print fid, name, width, height

            if not os.path.exists(os.path.join("data", "pcx_rgb")):
                os.makedirs(os.path.join("data", "pcx_rgb"))
                
            im = Image.frombuffer('RGB', (width, height), pcx[12:size+12],
                'raw', 'RGB', 0, 1)
            if os.path.exists(os.path.join("data", "pcx_rgb", name)):
                print "overwriting %s" % os.path.join("data", "pcx_rgb", name)
            im.save(os.path.join("data", "pcx_rgb", name), "PNG")
        elif ftype in (64, 65, 66, 67, 68, 69, 70, 71, 73,): #def animation
            #in 0.2% of all def files the internal def type does not match the
            #type given in the lod archive header but tests show that in this
            #case the type given in the def file is more important
            (ftype, width, height, sequences_count) = \
                struct.unpack("4i", pcx[0:16])
            palette = pcx[16:784]
            
            print fid, name, ftype
            
            #all def sequences are thrown into the same folder
            #there are no 65 def types - only 65 file types
            if ftype == 64:
                parent = os.path.join("data", "combat_spells", name)
            elif ftype == 66:
                parent = os.path.join("data", "combat_creatures", name)
            elif ftype == 67:
                parent = os.path.join("data", "advmap_objects", name)
            elif ftype == 68:
                parent = os.path.join("data", "advmap_heroes", name)
            elif ftype == 69:
                parent = os.path.join("data", "advmap_tiles", name)
            elif ftype == 70:
                parent = os.path.join("data", "cursors", name)
            elif ftype == 71:
                parent = os.path.join("data", "interface", name)
            elif ftype == 73:
                parent = os.path.join("data", "combat_heroes", name)
            else:
                raise NotImplementedError
            
            if not os.path.exists(parent):
                os.makedirs(parent)
            
            pos = 784
            for i in xrange(sequences_count):
                (index, length, unkown1, unkown2) = \
                    struct.unpack("4i", pcx[pos:pos+16])
                pos+=16
                
                folder = parent
                #create subfolder for defs with more than one sequence
                if sequences_count > 1:
                    folder = os.path.join(parent, str(i))
                
                    if not os.path.exists(folder):
                        os.makedirs(folder)
                
                pos+=13*length #read filenames
                
                offsets = struct.unpack("%di"%length, pcx[pos:pos+4*length])
                pos+=4*length
                
                lengths = []
                for j in xrange(length):
                    lengths.append(struct.unpack("i", pcx[offsets[j]:offsets[j]+4])[0])
                
                for j in xrange(length):
                    data = pcx[offsets[j]:offsets[j]+32+lengths[j]]
                    save_frame(folder, j, data, palette, width, height, name)
            
        elif ftype == 79: #msk file
            print fid, name, ftype
            save_file(fid, name, "msk", pcx)
        elif ftype == 80: #fnt file
            print fid, name, ftype
            save_file(fid, name, "fonts", pcx)
        elif ftype == 96: #pal file
            print fid, name, ftype
            save_file(fid, name, "palettes", pcx)
        else:
            raise Exception("type of %s not supported: %d"%(name, ftype))
    lod.close()

def snd_extract(filename):
    lod = open(filename)
    (files_count,) = struct.unpack("i", lod.read(4))
    print files_count
    
    if not os.path.exists(os.path.join("data", "sounds")):
        os.makedirs(os.path.join("data", "sounds"))
    
    for fid in xrange(files_count):
        lod.seek(4+(fid*48))
        filename = '.'.join([lod.read(40).split('\x00', 1)[0], "wav"])
        (offset, size) = struct.unpack("ii", lod.read(8))
        lod.seek(offset)
        wav = open(os.path.join("data", "sounds", filename), "w")
        wav.write(lod.read(size))
        wav.close()
        
    lod.close()

def vid_extract(filename):
    lod = open(filename)
    (files_count,) = struct.unpack("i", lod.read(4))
    print files_count
    
    offsets = []
    files = []
    for fid in xrange(files_count):
        lod.seek(4+(fid*44))
        files.append(lod.read(40).rstrip('\x00'))
        offsets.append(struct.unpack("i", lod.read(4))[0])
    offsets.append(os.stat(filename)[6])
    
    if not os.path.exists(os.path.join("data", "videos")):
        os.makedirs(os.path.join("data", "videos"))
    
    for i in xrange(len(offsets)-1): 
        print files[i]
        lod.seek(offsets[i])
        vid = open(os.path.join("data", "videos", files[i]), "w")
        vid.write(lod.read(offsets[i+1]-offsets[i]))
        vid.close()
    lod.close()


def main(args):
    path = "."
    if len(args) > 1:
        path = args[1]
    lod_extract(os.path.join(path, "H3bitmap.lod"))
    lod_extract(os.path.join(path, "H3ab_bmp.lod"))
    lod_extract(os.path.join(path, "H3sprite.lod"))
    lod_extract(os.path.join(path, "H3ab_spr.lod"))
    snd_extract(os.path.join(path, "Heroes3.snd"))
    snd_extract(os.path.join(path, "H3ab_ahd.snd"))
    vid_extract(os.path.join(path, "VIDEO.VID"))
    vid_extract(os.path.join(path, "H3ab_ahd.vid"))
    
    
if __name__ == '__main__':
    sys.exit(main(sys.argv))
