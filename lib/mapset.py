#!/usr/bin/env python
"""
    heroes renaissance
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

import pyglet
from ctypes import create_string_buffer, memmove
from lib import h3m
import os

class OrderedTextureGroup(pyglet.graphics.Group):
    def __init__(self, order, texture):
        super(OrderedTextureGroup, self).__init__()
        self.texture = texture
        self.order = order

    def set_state(self):
        pyglet.gl.glBindTexture(pyglet.gl.GL_TEXTURE_2D, self.texture.id)
    
    def unset_state(self):
        pass

    def __hash__(self):
        return hash((self.order, self.texture.id))

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
            self.order == other.order and
            self.texture.id == other.texture.id)

    def __repr__(self):
        return '%s(order=%d, id=%d)' % (self.__class__.__name__, self.order, self.texture.id)
        
    def __cmp__(self, other):
        if isinstance(other, OrderedTextureGroup):
            return cmp(self.order, other.order)
        return -1

class Animation(object):
    def __init__(self, tex_region, frames, objclass=None, overlay=False,
                 flip_x=False, flip_y=False):
        self.objclass = objclass
        self.overlay = overlay
        self.texgroup = tex_region.group
        self.atlas = tex_region.atlas
        if flip_x or flip_y:
            self.tex = tex_region.get_transform(flip_x=flip_x, flip_y=flip_y)
        else:    
            self.tex = tex_region
        self.__frames = []
        self.__hash = hash(frames[0])
        if len(frames) > 1:
            for img in frames:
                data_pitch = abs(img._current_pitch)
                buf = create_string_buffer(len(img._current_data))
                memmove(buf, img._current_data, len(img._current_data))
                data = buf.raw
                rows = [data[i:i + abs(data_pitch)] for i in
                       range(len(img._current_data)-abs(data_pitch),
                       -1, -abs(data_pitch))]
                self.__frames.append(''.join(rows))
        self.__animation = 0
    
    def next_frame(self):
        self.__animation = (self.__animation + 1) % len(self.__frames)
        return self.__frames[self.__animation]
    
    def __hash__(self):
        return self.__hash

    def __eq__(self, other):
        return self.__hash == other.__hash
    
    def __len__(self):
        return len(self.__frames)

class Animation_Object(object):
    def __init__(self, animation, group=None):
        if group != None:
            self.texgroup = group
        else:
            self.texgroup = animation.texgroup
        self.animation = animation
    
    @property
    def width(self):
        return self.animation.tex.width
    
    @property
    def height(self):
        return self.animation.tex.height
    
    @property
    def group(self):
        return self.texgroup
    
    @property
    def tex_coords(self):
        return self.animation.tex.tex_coords

class MapSet(object):
    def load_map_object(self, file, order=0):
        image = pyglet.image.load(None, file=pyglet.resource.file(file))
        try:
            texture_region = self.current_atlas.add(image)
        except pyglet.image.atlas.AllocatorException:
            self.current_atlas = pyglet.image.atlas.TextureAtlas(1024, 1024)
            texture_region = self.current_atlas.add(image)
            self.atlases.append(self.current_atlas)
        group = OrderedTextureGroup(order, self.current_atlas.texture)
        
        if group not in self.groups:
            self.groups.append(group)
        
        texture_region.group = self.groups.index(group)
        texture_region.atlas = self.atlases.index(self.atlases[-1])
        return texture_region

    def __init__(self, map_name):
        h3m_data = h3m.extract(os.path.join(pyglet.resource._default_loader._script_home,"maps","%s.h3m" % map_name))
        edge_map = [[] for i in range(len(h3m_data["upper_terrain"])+16)]
        for num in range(len(edge_map)):
            if num < 7 or num > len(edge_map)-8:
                line = []
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in range(len(h3m_data["upper_terrain"][0])+18)])
            elif num == 7:
                line = []
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in range(8)])
                line.append([-1, 16, 0, 0, 0, 0, 0])
                line.extend([[-1, 20+i%4, 0, 0, 0, 0, 0] for i in range(len(h3m_data["upper_terrain"][0]))])
                line.append([-1, 17, 0, 0, 0, 0, 0])
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in range(8)])
            elif num == len(edge_map)-8:
                line = []
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in range(8)])
                line.append([-1, 19, 0, 0, 0, 0, 0])
                line.extend([[-1, 28+i%4, 0, 0, 0, 0, 0] for i in range(len(h3m_data["upper_terrain"][0]))])
                line.append([-1, 18, 0, 0, 0, 0, 0])
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in range(8)])
            else:
                line = []
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in range(8)])
                line.append([-1, 32+num%4, 0, 0, 0, 0, 0])
                line.extend(h3m_data["upper_terrain"][num-8])
                line.append([-1, 24+num%4, 0, 0, 0, 0, 0])
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in range(8)])
            edge_map[num] = line
        h3m_data["upper_terrain"] = edge_map
        
        self.width = len(h3m_data["upper_terrain"][0])
        self.height = len(h3m_data["upper_terrain"])
        
        self.current_atlas = pyglet.image.atlas.TextureAtlas(1024, 1024)
        
        self.atlases = [self.current_atlas]
        
        self.groups = []
        
        self.__tiles = {}
        tile_textures = {}
        for y, line in enumerate(h3m_data["upper_terrain"]):
            for x, tile in enumerate(line):
                if tile[0] == -1: #edge
                    if "edg" not in list(tile_textures.keys()):
                        tile_textures["edg"] = [self.load_map_object('data/advmap_tiles/edg.def/%d.png'%i, 100) for i in range(36)]
                    self.__tiles[x,y] = [tile_textures["edg"][tile[1]]]
                elif tile[0] == 0: #dirt
                    if "dirttl" not in list(tile_textures.keys()):
                        tile_textures["dirttl"] = [self.load_map_object('data/advmap_tiles/dirttl.def/%d.png'%i, 0) for i in range(46)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["dirttl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["dirttl"][tile[1]].group
                        self.__tiles[x,y] = [new]
                    else:
                        self.__tiles[x,y] = [tile_textures["dirttl"][tile[1]]]
                elif tile[0] == 1: #sand
                    if "sandtl" not in list(tile_textures.keys()):
                        tile_textures["sandtl"] = [self.load_map_object('data/advmap_tiles/sandtl.def/%d.png'%i, 0) for i in range(24)]
                    self.__tiles[x,y] = [tile_textures["sandtl"][tile[1]]]
                elif tile[0] == 2: #grass
                    if "grastl" not in list(tile_textures.keys()):
                        tile_textures["grastl"] = [self.load_map_object('data/advmap_tiles/grastl.def/%d.png'%i, 0) for i in range(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["grastl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["grastl"][tile[1]].group
                        self.__tiles[x,y] = [new]
                    else:
                        self.__tiles[x,y] = [tile_textures["grastl"][tile[1]]]
                elif tile[0] == 3: #snow
                    if "snowtl" not in list(tile_textures.keys()):
                        tile_textures["snowtl"] = [self.load_map_object('data/advmap_tiles/snowtl.def/%d.png'%i, 0) for i in range(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["snowtl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["snowtl"][tile[1]].group
                        self.__tiles[x,y] = [new]
                    else:
                        self.__tiles[x,y] = [tile_textures["snowtl"][tile[1]]]
                elif tile[0] == 4: #swamp
                    if "swmptl" not in list(tile_textures.keys()):
                        tile_textures["swmptl"] = [self.load_map_object('data/advmap_tiles/swmptl.def/%d.png'%i, 0) for i in range(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["swmptl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["swmptl"][tile[1]].group
                        self.__tiles[x,y] = [new]
                    else:
                        self.__tiles[x,y] = [tile_textures["swmptl"][tile[1]]]
                elif tile[0] == 5: #rough
                    if "rougtl" not in list(tile_textures.keys()):
                        tile_textures["rougtl"] = [self.load_map_object('data/advmap_tiles/rougtl.def/%d.png'%i, 0) for i in range(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["rougtl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["rougtl"][tile[1]].group
                        self.__tiles[x,y] = [new]
                    else:
                        self.__tiles[x,y] = [tile_textures["rougtl"][tile[1]]]
                elif tile[0] == 7: #lava
                    if "lavatl" not in list(tile_textures.keys()):
                        tile_textures["lavatl"] = [self.load_map_object('data/advmap_tiles/lavatl.def/%d.png'%i, 0) for i in range(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["lavatl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["lavatl"][tile[1]].group
                        self.__tiles[x,y] = [new]
                    else:
                        self.__tiles[x,y] = [tile_textures["lavatl"][tile[1]]]
                elif tile[0] == 8: #water 12 anims
                    if "watrtl" not in list(tile_textures.keys()):
                        textures = [self.load_map_object('data/advmap_tiles/watrtl.def/%d/0.png'%i, 0) for i in range(33)]
                        images = [[pyglet.image.load(None, file=pyglet.resource.file('data/advmap_tiles/watrtl.def/%d/%d.png'%(i,j))) for j in range(12)] for i in range(33)]
                        tile_textures["watrtl"] = {
                            (0,0):[Animation_Object(Animation(texture, images[i])) for i, texture in enumerate(textures)],
                            (1,0):[Animation_Object(Animation(texture, images[i], flip_x=True)) for i, texture in enumerate(textures)],
                            (0,1):[Animation_Object(Animation(texture, images[i], flip_y=True)) for i, texture in enumerate(textures)],
                            (1,1):[Animation_Object(Animation(texture, images[i], flip_x=True, flip_y=True)) for i, texture in enumerate(textures)],
                        }
                    flip_x = (tile[6]>>0)&1
                    flip_y = (tile[6]>>1)&1
                    self.__tiles[x,y] = [tile_textures["watrtl"][flip_x, flip_y][tile[1]]]
                elif tile[0] == 9: #rock
                    if "rocktl" not in list(tile_textures.keys()):
                        tile_textures["rocktl"] = [self.load_map_object('data/advmap_tiles/rocktl.def/%d.png'%i, 0) for i in range(48)]
                    self.__tiles[x,y] = [tile_textures["rocktl"][tile[1]]]
                else:
                    raise NotImplementedError
                
                if tile[2] == 0: #no river
                    pass
                elif tile[2] == 1: #clrrvr 12 anims
                    if "clrrvr" not in list(tile_textures.keys()):
                        textures = [self.load_map_object('data/advmap_tiles/clrrvr.def/%d/0.png'%i, 1) for i in range(13)]
                        images = [[pyglet.image.load(None, file=pyglet.resource.file('data/advmap_tiles/clrrvr.def/%d/%d.png'%(i,j))) for j in range(12)] for i in range(13)]
                        tile_textures["clrrvr"] = {
                            (0,0):[Animation_Object(Animation(texture, images[i])) for i, texture in enumerate(textures)],
                            (1,0):[Animation_Object(Animation(texture, images[i], flip_x=True)) for i, texture in enumerate(textures)],
                            (0,1):[Animation_Object(Animation(texture, images[i], flip_y=True)) for i, texture in enumerate(textures)],
                            (1,1):[Animation_Object(Animation(texture, images[i], flip_x=True, flip_y=True)) for i, texture in enumerate(textures)],
                        }
                    flip_x = (tile[6]>>2)&1
                    flip_y = (tile[6]>>3)&1
                    self.__tiles[x,y].append(tile_textures["clrrvr"][flip_x, flip_y][tile[3]])
                elif tile[2] == 2: #icyrvr
                    if "icyrvr" not in list(tile_textures.keys()):
                        tile_textures["icyrvr"] = [self.load_map_object('data/advmap_tiles/icyrvr.def/%d.png'%i, 1) for i in range(13)]
                    flip_x = bool(tile[6] & 4)
                    flip_y = bool(tile[6] & 8)
                    if flip_x or flip_y:
                        new = tile_textures["icyrvr"][tile[3]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["icyrvr"][tile[3]].group
                        self.__tiles[x, y].append(new)
                    else:
                        self.__tiles[x, y].append(tile_textures["icyrvr"][tile[3]])
                elif tile[2] == 3: #mudrvr
                    if "mudrvr" not in list(tile_textures.keys()):
                        textures = [self.load_map_object('data/advmap_tiles/mudrvr.def/%d/0.png'%i, 1) for i in range(13)]
                        images = [[pyglet.image.load(None, file=pyglet.resource.file('data/advmap_tiles/clrrvr.def/%d/%d.png'%(i,j))) for j in range(12)] for i in range(13)]
                        tile_textures["mudrvr"] = {
                            (0,0):[Animation_Object(Animation(texture, images[i])) for i, texture in enumerate(textures)],
                            (1,0):[Animation_Object(Animation(texture, images[i], flip_x=True)) for i, texture in enumerate(textures)],
                            (0,1):[Animation_Object(Animation(texture, images[i], flip_y=True)) for i, texture in enumerate(textures)],
                            (1,1):[Animation_Object(Animation(texture, images[i], flip_x=True, flip_y=True)) for i, texture in enumerate(textures)],
                        }
                    flip_x = (tile[6]>>2)&1
                    flip_y = (tile[6]>>3)&1
                    self.__tiles[x,y].append(tile_textures["mudrvr"][flip_x, flip_y][tile[3]])
                elif tile[2] == 4: #lavrvr
                    if "lavrvr" not in list(tile_textures.keys()):
                        textures = [self.load_map_object('data/advmap_tiles/lavrvr.def/%d/0.png'%i, 1) for i in range(13)]
                        images = [[pyglet.image.load(None, file=pyglet.resource.file('data/advmap_tiles/clrrvr.def/%d/%d.png'%(i,j))) for j in range(9)] for i in range(13)]
                        tile_textures["lavrvr"] = {
                            (0,0):[Animation_Object(Animation(texture, images[i])) for i, texture in enumerate(textures)],
                            (1,0):[Animation_Object(Animation(texture, images[i], flip_x=True)) for i, texture in enumerate(textures)],
                            (0,1):[Animation_Object(Animation(texture, images[i], flip_y=True)) for i, texture in enumerate(textures)],
                            (1,1):[Animation_Object(Animation(texture, images[i], flip_x=True, flip_y=True)) for i, texture in enumerate(textures)],
                        }
                    flip_x = (tile[6]>>2)&1
                    flip_y = (tile[6]>>3)&1
                    self.__tiles[x,y].append(tile_textures["lavrvr"][flip_x, flip_y][tile[3]])
                else:
                    raise NotImplementedError(tile[2])
                
                if tile[4] == 0: #no road
                    pass
                elif tile[4] == 1: #dirtrd
                    if "dirtrd" not in list(tile_textures.keys()):
                        tile_textures["dirtrd"] = [self.load_map_object('data/advmap_tiles/dirtrd.def/%d.png'%i, 1) for i in range(17)]
                    flip_x = bool(tile[6] & 16)
                    flip_y = bool(tile[6] & 32)
                    if flip_x or flip_y:
                        new = tile_textures["dirtrd"][tile[5]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["dirtrd"][tile[5]].group
                        self.__tiles[x, y].append(new)
                    else:
                        self.__tiles[x, y].append(tile_textures["dirtrd"][tile[5]])
                elif tile[4] == 2: #gravrd
                    if "gravrd" not in list(tile_textures.keys()):
                        tile_textures["gravrd"] = [self.load_map_object('data/advmap_tiles/gravrd.def/%d.png'%i, 1) for i in range(17)]
                    flip_x = bool(tile[6] & 16)
                    flip_y = bool(tile[6] & 32)
                    if flip_x or flip_y:
                        new = tile_textures["gravrd"][tile[5]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["gravrd"][tile[5]].group
                        self.__tiles[x, y].append(new)
                    else:
                        self.__tiles[x, y].append(tile_textures["gravrd"][tile[5]])
                elif tile[4] == 3: #cobbrd
                    if "cobbrd" not in list(tile_textures.keys()):
                        tile_textures["cobbrd"] = [self.load_map_object('data/advmap_tiles/cobbrd.def/%d.png'%i, 1) for i in range(17)]
                    flip_x = bool(tile[6] & 16)
                    flip_y = bool(tile[6] & 32)
                    if flip_x or flip_y:
                        new = tile_textures["cobbrd"][tile[5]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["cobbrd"][tile[5]].group
                        self.__tiles[x, y].append(new)
                    else:
                        self.__tiles[x, y].append(tile_textures["cobbrd"][tile[5]])
                else:
                    raise NotImplementedError(tile[4])
        
        images = []
        for order, obj in enumerate(h3m_data["objects"]):
            imgs = []
            i = 0
            while 1:
                imgs.append(pyglet.image.load(None, file=pyglet.resource.file("data/advmap_objects/" + obj["filename"] + "/%d.png"%i)))
                i += 1
                if "data/advmap_objects/" + obj["filename"] + "/%d.png" % i not in list(pyglet.resource._default_loader._index.keys()):
                    break;
            images.append((imgs, obj["class"], obj["overlay"], order))
        
        self.objects = []
        for imgs in sorted(images, key=lambda i:i[0][0].height, reverse=True):
            try:
                texture = self.current_atlas.add(imgs[0][0])
            except pyglet.image.atlas.AllocatorException:
                self.current_atlas = pyglet.image.atlas.TextureAtlas(1024, 1024)
                texture = self.current_atlas.add(imgs[0][0])
                self.atlases.append(self.current_atlas)
            texture.group = None
            texture.atlas = self.atlases.index(self.atlases[-1])
            self.objects.append((Animation(texture, imgs[0], objclass=imgs[1], overlay=imgs[2]), imgs[3]))
        
        self.objects = [i[0] for i in sorted(self.objects, key=lambda i:i[1])]
        
        for obj in [i for i in h3m_data["tunedobj"] if i["z"]==0]:
            # order objects by row in which they are placed
            # 8 levels offset because of objects 6 tiles high
            order = obj["y"] + 8
            # if the overlay attribute is set, object is drawn below all
            # objects ove it - so substract its hight
            if self.objects[obj["id"]].overlay:
                order = order - self.objects[obj["id"]].tex.height // 32
            # each row two levels - woods and mountains in the back and the
            # rest in front
            order *= 2
            # put wood and mountains behind other objects on the same level
            if self.objects[obj["id"]].objclass in [119, 134, 135, 137, 155, 199]:
                order -= 1
            group = OrderedTextureGroup(order, self.atlases[self.objects[obj["id"]].tex.atlas].texture)
            if group not in self.groups:
                self.groups.append(group)
            group = self.groups.index(group)
            self.__tiles[obj["x"] + 9, obj["y"] + 8].append(Animation_Object(self.objects[obj["id"]], group))
    
    def get_tiles(self, tiles_x, tiles_y, div_x, div_y):
        for y in range(tiles_y - 1, -6, -1):
            y1 = y * 32
            for x in range(tiles_x + 4, -1, -1):
                for obj in self.__tiles.get((x - div_x, div_y - y), []):
                    x1 = x * 32 - obj.width + 32
                    x2 = x1 + obj.width
                    y2 = y1 + obj.height
                    yield obj, [x1, y1, x2, y1, x2, y2, x1, y2]
