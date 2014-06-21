#!/usr/bin/python
"""
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

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import demjson as json
        json.loads = json.decode
        json.dumps = json.encode

IF_BOTTOM = 48
IF_RIGHT = 200
IF_TOP = IF_LEFT = 8

class Animation(object):
    def __init__(self, frames):
        self.__frames = frames
        self.__animation = 0
        self.width = frames[0].width
        self.height = frames[0].height
        self.z = frames[0].z
    
    def next_frame(self):
        self.__animation = (self.__animation+1)%len(self.__frames)
    
    def get_tex_coords(self):
        return self.__frames[self.__animation].tex_coords
    
    tex_coords = property(get_tex_coords)
    
    def get_group(self):
        return self.__frames[self.__animation].group
        
    group = property(get_group)

class MapSet(object):
    def load_map_object(self, file, order=0):
        image = pyglet.image.load(None, file=pyglet.resource.file(file))
        try:
            texture_region = self.current_atlas.add(image)
        except pyglet.image.atlas.AllocatorException:
            self.current_atlas = pyglet.image.atlas.TextureAtlas(1024, 1024)
            print "atlas"
            texture_region = self.current_atlas.add(image)
        group = pyglet.graphics.TextureGroup(self.current_atlas.texture)
        
        if group not in self.groups:
            self.groups.append(group)
        
        texture_region.group = self.groups.index(group)
        texture_region.z = order
        return texture_region

    def __init__(self, loaded_map, objects, tunedobj):
        self.width = len(loaded_map[0])
        self.height = len(loaded_map)
        
        self.current_atlas = pyglet.image.atlas.TextureAtlas(1024, 1024)
        print "atlas"
        
        self.groups = []
        
        self.tiles = {}
        tile_textures = {}
        for y, line in enumerate(loaded_map):
            for x, tile in enumerate(line):
                if tile[0] == -1: #edge
                    if "edg" not in tile_textures.keys():
                        tile_textures["edg"] = [self.load_map_object('data/advmap_tiles/edg.def/%d.png'%i, 100) for i in xrange(36)]
                    self.tiles[x,y] = [tile_textures["edg"][tile[1]]]
                elif tile[0] == 0: #dirt
                    if "dirttl" not in tile_textures.keys():
                        tile_textures["dirttl"] = [self.load_map_object('data/advmap_tiles/dirttl.def/%d.png'%i, 0) for i in xrange(46)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["dirttl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["dirttl"][tile[1]].group
                        self.tiles[x,y] = [new]
                    else:
                        self.tiles[x,y] = [tile_textures["dirttl"][tile[1]]]
                elif tile[0] == 1: #sand
                    if "sandtl" not in tile_textures.keys():
                        tile_textures["sandtl"] = [self.load_map_object('data/advmap_tiles/sandtl.def/%d.png'%i, 0) for i in xrange(24)]
                    self.tiles[x,y] = [tile_textures["sandtl"][tile[1]]]
                elif tile[0] == 2: #grass
                    if "grastl" not in tile_textures.keys():
                        tile_textures["grastl"] = [self.load_map_object('data/advmap_tiles/grastl.def/%d.png'%i, 0) for i in xrange(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["grastl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["grastl"][tile[1]].group
                        self.tiles[x,y] = [new]
                    else:
                        self.tiles[x,y] = [tile_textures["grastl"][tile[1]]]
                elif tile[0] == 3: #snow
                    if "snowtl" not in tile_textures.keys():
                        tile_textures["snowtl"] = [self.load_map_object('data/advmap_tiles/snowtl.def/%d.png'%i, 0) for i in xrange(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["snowtl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["snowtl"][tile[1]].group
                        self.tiles[x,y] = [new]
                    else:
                        self.tiles[x,y] = [tile_textures["snowtl"][tile[1]]]
                elif tile[0] == 4: #swamp
                    if "swmptl" not in tile_textures.keys():
                        tile_textures["swmptl"] = [self.load_map_object('data/advmap_tiles/swmptl.def/%d.png'%i, 0) for i in xrange(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["swmptl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["swmptl"][tile[1]].group
                        self.tiles[x,y] = [new]
                    else:
                        self.tiles[x,y] = [tile_textures["swmptl"][tile[1]]]
                elif tile[0] == 5: #rough
                    if "rougtl" not in tile_textures.keys():
                        tile_textures["rougtl"] = [self.load_map_object('data/advmap_tiles/rougtl.def/%d.png'%i, 0) for i in xrange(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["rougtl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["rougtl"][tile[1]].group
                        self.tiles[x,y] = [new]
                    else:
                        self.tiles[x,y] = [tile_textures["rougtl"][tile[1]]]
                elif tile[0] == 7: #lava
                    if "lavatl" not in tile_textures.keys():
                        tile_textures["lavatl"] = [self.load_map_object('data/advmap_tiles/lavatl.def/%d.png'%i, 0) for i in xrange(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["lavatl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["lavatl"][tile[1]].group
                        self.tiles[x,y] = [new]
                    else:
                        self.tiles[x,y] = [tile_textures["lavatl"][tile[1]]]
                elif tile[0] == 8: #water
                    if "watrtl" not in tile_textures.keys():
                        tile_textures["watrtl"] = []
                        for j in xrange(33):
                            tile_textures["watrtl"].append([self.load_map_object('data/advmap_tiles/watrtl.def/%d/%d.png'%(j,i), 0) for i in xrange(12)])
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        tiles = []
                        for watrtl in tile_textures["watrtl"][tile[1]]:
                            new = watrtl.get_transform(flip_x=flip_x, flip_y=flip_y)
                            new.group = watrtl.group
                            tiles.append(new)
                        self.tiles[x,y] = [Animation(tiles)]
                    else:
                        self.tiles[x,y] = [Animation(tile_textures["watrtl"][tile[1]])]
                elif tile[0] == 9: #rock
                    if "rocktl" not in tile_textures.keys():
                        tile_textures["rocktl"] = [self.load_map_object('data/advmap_tiles/rocktl.def/%d.png'%i, 0) for i in xrange(48)]
                    self.tiles[x,y] = [tile_textures["rocktl"][tile[1]]]
                else:
                    raise NotImplementedError
                
                if tile[2] == 0: #no river
                    pass
                elif tile[2] == 1: #clrrvr
                    if "clrrvr" not in tile_textures.keys():
                        tile_textures["clrrvr"] = [[self.load_map_object('data/advmap_tiles/clrrvr.def/%d/%d.png'%(i, j), 1) for j in xrange(12)] for i in xrange(13)]
                    flip_x = bool(tile[6] & 4)
                    flip_y = bool(tile[6] & 8)
                    if flip_x or flip_y:
                        tiles = []
                        for clrrvr in tile_textures["clrrvr"][tile[3]]:
                            new = clrrvr.get_transform(flip_x=flip_x, flip_y=flip_y)
                            new.group = clrrvr.group
                            tiles.append(new)
                        self.tiles[x, y].append(Animation(tiles))
                    else:
                        self.tiles[x, y].append(Animation(tile_textures["clrrvr"][tile[3]]))
                elif tile[2] == 2: #icyrvr
                    if "icyrvr" not in tile_textures.keys():
                        tile_textures["icyrvr"] = [self.load_map_object('data/advmap_tiles/icyrvr.def/%d.png'%i, 1) for i in xrange(13)]
                    flip_x = bool(tile[6] & 4)
                    flip_y = bool(tile[6] & 8)
                    if flip_x or flip_y:
                        new = tile_textures["icyrvr"][tile[3]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["icyrvr"][tile[3]].group
                        self.tiles[x, y].append(new)
                    else:
                        self.tiles[x, y].append(tile_textures["icyrvr"][tile[3]])
                elif tile[2] == 3: #mudrvr
                    if "mudrvr" not in tile_textures.keys():
                        tile_textures["mudrvr"] = [[self.load_map_object('data/advmap_tiles/mudrvr.def/%d/%d.png'%(i, j), 1) for j in xrange(12)] for i in xrange(13)]
                    flip_x = bool(tile[6] & 4)
                    flip_y = bool(tile[6] & 8)
                    if flip_x or flip_y:
                        tiles = []
                        for mudrvr in tile_textures["mudrvr"][tile[3]]:
                            new = mudrvr.get_transform(flip_x=flip_x, flip_y=flip_y)
                            new.group = mudrvr.group
                            tiles.append(new)
                        self.tiles[x, y].append(Animation(tiles))
                    else:
                        self.tiles[x, y].append(Animation(tile_textures["mudrvr"][tile[3]]))
                elif tile[2] == 4: #lavrvr
                    if "lavrvr" not in tile_textures.keys():
                        tile_textures["lavrvr"] = [[self.load_map_object('data/advmap_tiles/lavrvr.def/%d/%d.png'%(i, j), 1) for j in xrange(9)] for i in xrange(13)]
                    flip_x = bool(tile[6] & 4)
                    flip_y = bool(tile[6] & 8)
                    if flip_x or flip_y:
                        tiles = []
                        for lavrvr in tile_textures["lavrvr"][tile[3]]:
                            new = lavrvr.get_transform(flip_x=flip_x, flip_y=flip_y)
                            new.group = lavrvr.group
                            tiles.append(new)
                        self.tiles[x, y].append(Animation(tiles))
                    else:
                        self.tiles[x, y].append(Animation(tile_textures["lavrvr"][tile[3]]))
                else:
                    raise NotImplementedError, tile[2]
                
                if tile[4] == 0: #no road
                    pass
                elif tile[4] == 1: #dirtrd
                    if "dirtrd" not in tile_textures.keys():
                        tile_textures["dirtrd"] = [self.load_map_object('data/advmap_tiles/dirtrd.def/%d.png'%i, 1) for i in xrange(17)]
                    flip_x = bool(tile[6] & 16)
                    flip_y = bool(tile[6] & 32)
                    if flip_x or flip_y:
                        new = tile_textures["dirtrd"][tile[5]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["dirtrd"][tile[5]].group
                        self.tiles[x, y].append(new)
                    else:
                        self.tiles[x, y].append(tile_textures["dirtrd"][tile[5]])
                elif tile[4] == 2: #gravrd
                    if "gravrd" not in tile_textures.keys():
                        tile_textures["gravrd"] = [self.load_map_object('data/advmap_tiles/gravrd.def/%d.png'%i, 1) for i in xrange(17)]
                    flip_x = bool(tile[6] & 16)
                    flip_y = bool(tile[6] & 32)
                    if flip_x or flip_y:
                        new = tile_textures["gravrd"][tile[5]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["gravrd"][tile[5]].group
                        self.tiles[x, y].append(new)
                    else:
                        self.tiles[x, y].append(tile_textures["gravrd"][tile[5]])
                elif tile[4] == 3: #cobbrd
                    if "cobbrd" not in tile_textures.keys():
                        tile_textures["cobbrd"] = [self.load_map_object('data/advmap_tiles/cobbrd.def/%d.png'%i, 1) for i in xrange(17)]
                    flip_x = bool(tile[6] & 16)
                    flip_y = bool(tile[6] & 32)
                    if flip_x or flip_y:
                        new = tile_textures["cobbrd"][tile[5]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["cobbrd"][tile[5]].group
                        self.tiles[x, y].append(new)
                    else:
                        self.tiles[x, y].append(tile_textures["cobbrd"][tile[5]])
                else:
                    raise NotImplementedError, tile[4]
        
        images = []
        for order, obj in enumerate(objects):
            imgs = []
            i = 0
            while 1:
                imgs.append(pyglet.image.load(None, file=pyglet.resource.file("data/advmap_objects/"+obj["filename"]+"/%d.png"%i)))
                i+=1
                if "data/advmap_objects/"+obj["filename"]+"/%d.png"%i not in pyglet.resource._default_loader._index.keys():
                    break;
            images.append((imgs, order))
        
        self.objects = []
        for imgs in sorted(images, key=lambda i:i[0][0].height, reverse=True):
            textures = []
            try:
                textures = [self.current_atlas.add(img) for img in imgs[0]]
            except pyglet.image.atlas.AllocatorException:
                self.current_atlas = pyglet.image.atlas.TextureAtlas(1024, 1024)
                print "atlas"
                textures = [self.current_atlas.add(img) for img in imgs[0]]
            group = pyglet.graphics.TextureGroup(self.current_atlas.texture)
            if group not in self.groups:
                self.groups.append(group)
            group = self.groups.index(group)
            for texture in textures:
                texture.group = group
                texture.z = 2
            self.objects.append((textures, imgs[1]))
        
        self.objects = [i[0] for i in sorted(self.objects, key=lambda i:i[1])]
        
        self.tunedobj = {}
        for obj in [i for i in tunedobj if i["z"]==0]:
            if len(self.objects[obj["id"]]) == 1:
                self.tiles[obj["x"]+9,obj["y"]+8].append(self.objects[obj["id"]][0])
            else:
                self.tiles[obj["x"]+9,obj["y"]+8].append(Animation(self.objects[obj["id"]]))
        
class MapView(object):
    def __init__(self, mapset, window):
        self.window = window
        self.mapset = mapset
        
        self._first_time_init()
        self._init_view()
        
        #mouse position
        self.label = pyglet.text.Label('',
                font_name="",
                font_size=36,
                bold=True,
                color=(128, 128, 128, 128),
                x=self.window.width-10, y=0,
                anchor_x='right', anchor_y='bottom')
        
        #pyglet.clock.schedule_interval(self.animate_water, 1/6.0)
        pyglet.clock.schedule_interval(self.update, 1/60.0)
    
    def _first_time_init(self):
        self.tile_size = 32
        self.viewport_x = self.window.width-IF_RIGHT-IF_LEFT
        self.viewport_y = self.window.height-IF_BOTTOM-IF_TOP
        #center map
        self.global_x = (self.mapset.width*self.tile_size-self.viewport_x+self.tile_size)//2
        self.global_y = (self.mapset.height*self.tile_size)//2-(self.viewport_y//2)+(self.tile_size//2)
        
        self.mouse_x = self.mouse_dx = 0
        self.mouse_y = self.mouse_dy = 0
    
    def _init_view(self):
        #step one tile
        self.steps = self.tile_size
        
        self.viewport_x = self.window.width-IF_RIGHT-IF_LEFT
        self.viewport_y = self.window.height-IF_BOTTOM-IF_TOP
        
        #center map when viewport is too large, else check if map still fills
        #whole viewport and if not adjust position accordingly
        self.center_x = False
        if self.mapset.width*self.tile_size < self.viewport_x:
            self.center_x = True
            self.global_x = (self.mapset.width*self.tile_size)//2-(self.viewport_x//2)
        elif self.global_x > self.tile_size*self.mapset.width-self.viewport_x:
            self.global_x = self.tile_size*self.mapset.width-self.viewport_x
        elif self.global_x < 0:
            self.global_x = 0
        
        self.center_y = False
        if self.mapset.height*self.tile_size < self.viewport_y:
            self.center_y = True
            self.global_y = (self.mapset.height*self.tile_size)//2-(self.viewport_y//2)
        elif self.global_y > self.tile_size*self.mapset.height-self.viewport_y:
            self.global_y = self.tile_size*self.mapset.height-self.viewport_y
        elif self.global_y < 0:
            self.global_y = 0
        
        #drawn tiles
        self.tiles_x = min((self.viewport_x//self.tile_size)+2, self.mapset.width)
        self.tiles_y = min((self.viewport_y//self.tile_size)+2, self.mapset.height)
        
        #undrawn map size
        self.undrawn_x = self.tile_size*(self.mapset.width-self.tiles_x)
        self.undrawn_y = self.tile_size*(self.mapset.height-self.tiles_y)
        #size of full undrawn steps
        self.undrawn_steps_x = self.steps*(self.undrawn_x//self.steps)
        self.undrawn_steps_y = self.steps*(self.undrawn_y//self.steps)
        
        self.batch = pyglet.graphics.Batch()
        
        self.view_x = 0
        self.view_y = 0
        self.dx = 0
        self.dy = 0
        
        #here we translate the global map position so we can draw with it
        trans_global_x = self.steps-self.global_x
        trans_global_y = self.steps-self.global_y
        
        if trans_global_x < -self.undrawn_steps_x:
            mod_x = trans_global_x+self.undrawn_x
        elif trans_global_x < self.steps:
            mod_x = trans_global_x%self.steps
        else:
            mod_x = trans_global_x
        
        if trans_global_y < -self.undrawn_steps_y:
            mod_y = trans_global_y+self.undrawn_y
        elif trans_global_y < self.steps:
            mod_y = trans_global_y%self.steps
        else:
            mod_y = trans_global_y
        
        self.div_x = (trans_global_x-mod_x)//self.tile_size
        self.div_y = (trans_global_y-mod_y)//self.tile_size+self.mapset.height-1
        
        self.vl_objects = [None for i, value in enumerate(self.mapset.groups)]
        vertices = [[] for i, value in enumerate(self.mapset.groups)]
        tex_coords = [[] for i, value in enumerate(self.mapset.groups)]
        count = [0 for i, value in enumerate(self.mapset.groups)]
        
#        for y in xrange(self.tiles_y-1, -6, -1):
        for y in xrange(self.tiles_y):
            y1 = y*32+IF_BOTTOM
            for x in xrange(self.tiles_x+5-1, -1, -1):
                for obj in self.mapset.tiles.get((x-self.div_x, self.div_y-y), []):
                    x1 = x*32+IF_LEFT-obj.width+32
                    x2 = x1+obj.width
                    y2 = y1+obj.height
                    z = obj.z*0.01
                    vertices[obj.group].extend([x1, y1, z, x2, y1, z, x2, y2, z, x1, y2, z])
                    tex_coords[obj.group].extend(obj.tex_coords)
                    count[obj.group]+=4
        
        for i, group in enumerate(self.mapset.groups):
            if count[i] != 0:
                self.vl_objects[i] = self.batch.add(count[i], pyglet.gl.GL_QUADS,
                        group,
                        ('v3f', vertices[i]),
                        ('t3f', tex_coords[i]),
                        ('c4B', (255,255,255,255)*count[i]))
        
        self.view_x = mod_x-self.steps-(self.tile_size-32)//4
        self.view_y = mod_y-self.steps-((self.tile_size-32)*3)//2
    
    def on_draw(self):
        pyglet.gl.glClear(pyglet.gl.GL_COLOR_BUFFER_BIT | pyglet.gl.GL_DEPTH_BUFFER_BIT)
        #pyglet.gl.glClear(pyglet.gl.GL_COLOR_BUFFER_BIT)
        pyglet.gl.glEnable(pyglet.gl.GL_DEPTH_TEST)
#        pyglet.gl.glDepthFunc(pyglet.gl.GL_ALWAYS)
        pyglet.gl.glDepthMask(pyglet.gl.GL_TRUE);

#        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        #pyglet.gl.glBlendFunc(pyglet.gl.GL_ONE_MINUS_DST_ALPHA, pyglet.gl.GL_DST_ALPHA)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        
        #pyglet.gl.glAlphaFunc(pyglet.gl.GL_NOTEQUAL, 0)
        #pyglet.gl.glEnable(pyglet.gl.GL_ALPHA_TEST)
        
        pyglet.gl.glPushMatrix()
        pyglet.gl.glTranslatef(self.view_x, self.view_y, 0)
        pyglet.gl.glScalef(self.tile_size/32.0, self.tile_size/32.0, 1.0)
        self.batch.draw()
        pyglet.gl.glPopMatrix()
        pyglet.gl.glLoadIdentity()
#        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
#        pyglet.gl.glColor4f(1, 0, 1, 1)
#        pyglet.gl.glRectf(0, 0, self.window.width, IF_BOTTOM)
#        pyglet.gl.glRectf(self.window.width-IF_RIGHT, 0, self.window.width, self.window.height)
#        pyglet.gl.glRectf(0, self.window.height-IF_TOP, self.window.width, self.window.height)
#        pyglet.gl.glRectf(0, 0, IF_LEFT, self.window.height)
        self.label.draw()
    
    def _move(self, dx, dy):
        #here we translate the global map position so we can draw with it
        trans_global_x = self.steps-self.global_x
        trans_global_y = self.steps-self.global_y
        
        new_global_x = trans_global_x+dx
        new_global_y = trans_global_y+dy
        
        if self.global_x-dx < 0:
            new_global_x = self.steps
        if self.global_y-dy < 0:
            new_global_y = self.steps
        if dx-self.global_x < -self.tile_size*self.mapset.width+self.viewport_x:
            new_global_x = -self.tile_size*self.mapset.width+self.viewport_x+self.steps
        if dy-self.global_y < -self.tile_size*self.mapset.height+self.viewport_y:
            new_global_y = -self.tile_size*self.mapset.height+self.viewport_y+self.steps
        
        retex = False
        
        if new_global_x < -self.undrawn_steps_x:
            mod_x = new_global_x+self.undrawn_x
            if trans_global_x >= -self.undrawn_steps_x:
                retex = True
        elif new_global_x < self.steps:
            div_x, mod_x = divmod(new_global_x, self.steps)
            retex = div_x != trans_global_x//self.steps or retex
        else:
            mod_x = new_global_x
        
        if new_global_y < -self.undrawn_steps_y:
            mod_y = new_global_y+self.undrawn_y
            if trans_global_y >= -self.undrawn_steps_y:
                retex = True
        elif new_global_y < self.steps:
            div_y, mod_y = divmod(new_global_y, self.steps)
            retex = div_y != trans_global_y//self.steps or retex
        else:
            mod_y = new_global_y
        
        if retex:
            self.div_x = (new_global_x-mod_x)//self.tile_size
            self.div_y = (new_global_y-mod_y)//self.tile_size+self.mapset.height-1
            vertices = [[] for i, value in enumerate(self.mapset.groups)]
            tex_coords = [[] for i, value in enumerate(self.mapset.groups)]
            count = [0 for i, value in enumerate(self.mapset.groups)]
            for y in xrange(self.tiles_y-1, -6, -1):
                y1 = y*32+IF_BOTTOM
                for x in xrange(self.tiles_x+5-1, -1, -1):
                    for obj in self.mapset.tiles.get((x-self.div_x, self.div_y-y), []):
                        x1 = x*32+IF_LEFT-obj.width+32
                        x2 = x1+obj.width
                        y2 = y1+obj.height
                        tex_coords[obj.group].extend(obj.tex_coords)
                        z = -y*0.01
                        vertices[obj.group].extend([x1, y1, z, x2, y1, z, x2, y2, z, x1, y2, z])
                        count[obj.group]+=4
            
            for i, group in enumerate(self.mapset.groups):
                if count[i] == 0:
                    if self.vl_objects[i] is None:
                        pass
                    else:
                        self.vl_objects[i].delete()
                        self.vl_objects[i] = None
                else:
                    if self.vl_objects[i] is None:
                        self.vl_objects[i] = self.batch.add(count[i], pyglet.gl.GL_QUADS,
                                group,
                                ('v3f', vertices[i]),
                                ('t3f', tex_coords[i]),
                                ('c4B', (255,255,255,255)*count[i]))
                    else:
                        self.vl_objects[i].resize(count[i])
                        self.vl_objects[i].tex_coords = tex_coords[i]
                        self.vl_objects[i].vertices = vertices[i]
                        self.vl_objects[i].colors = (255,255,255,255)*count[i]
        
        if not self.center_x:
            self.view_x = mod_x-self.steps-(self.tile_size-32)//4
            self.global_x = self.steps-new_global_x
        if not self.center_y:
            self.view_y = mod_y-self.steps-((self.tile_size-32)*3)//2
            self.global_y = self.steps-new_global_y
    
    def update(self, dt):
        try:
            if self.window.keys[pyglet.window.key.LCTRL] and \
               any([self.window.keys[pyglet.window.key.UP],
                    self.window.keys[pyglet.window.key.DOWN],
                    self.window.keys[pyglet.window.key.LEFT],
                    self.window.keys[pyglet.window.key.RIGHT]]):
                
                if self.window.keys[pyglet.window.key.LEFT]:
                    x = 1
                elif self.window.keys[pyglet.window.key.RIGHT]:
                    x = -1
                else:
                    x = 0
                
                if self.window.keys[pyglet.window.key.UP]:
                    y = -1
                elif self.window.keys[pyglet.window.key.DOWN]:
                    y = 1
                else:
                    y = 0
                self.dx += x*8
                self.dy += y*8
            elif self.window.keys[pyglet.window.key.PLUS] and \
                 self.tile_size < 32:
                self.tile_size+=8
                self._init_view()
            elif self.window.keys[pyglet.window.key.MINUS] and \
                 self.tile_size > 16:
                self.tile_size-=8
                self._init_view()
        except KeyError:
            pass
        if self.dx or self.dy:
            self._move(self.dx, self.dy)
            self.dx = 0
            self.dy = 0
        #mouse position:
        if self.mouse_x != self.mouse_dx or self.mouse_y != self.mouse_dy:
            self.mouse_x = self.mouse_dx
            self.mouse_y = self.mouse_dy
            x = (self.mouse_x-IF_LEFT-self.view_x
                -(self.tile_size-32)//4)//self.tile_size
            y = (self.mouse_y-IF_BOTTOM-self.view_y
                -((self.tile_size-32)*3)//2)//self.tile_size
            self.label.text = "%03d %03d"%(x-self.div_x, self.div_y-y)
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.dx += dx
        self.dy += dy
        self.mouse_dx = x
        self.mouse_dy = y
        return pyglet.event.EVENT_HANDLED
    
    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_dx = x
        self.mouse_dy = y
        return pyglet.event.EVENT_HANDLED
    
    def on_resize(self, width, height):
        self._init_view()
    
    def animate_water(self, dt):
        tex_coords = [[] for i, value in enumerate(self.mapset.groups)]
        for y in xrange(self.tiles_y-1, -6, -1):
            for x in xrange(self.tiles_x+5-1, -1, -1):
                for obj in self.mapset.tiles.get((x-self.div_x, self.div_y-y), []):
                    if isinstance(obj, Animation):
                        obj.next_frame()
                    tex_coords[obj.group].extend(obj.tex_coords)
        for i, group in enumerate(self.mapset.groups):
            if len(tex_coords[i]) != 0:
                self.vl_objects[i].tex_coords = tex_coords[i]

class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(1280, 1024, resizable=True, vsync=False)
        self.keys = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.keys)
        self.fps = pyglet.clock.ClockDisplay()
        pyglet.clock.schedule(lambda dt: None)
    
    def on_draw(self):
        self.fps.draw()
    
    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.F11:
            self.set_fullscreen(fullscreen=not self.fullscreen)
        elif symbol == pyglet.window.key.P:
            pyglet.image.get_buffer_manager().get_color_buffer().save('screenshot.png', encoder=PNGRGBEncoder())

class PNGRGBEncoder(pyglet.image.codecs.ImageEncoder):
    def encode(self, image, file, filename):
        import Image
        image = image.get_image_data()
        format = image.format
        pitch = -(image.width * len(format))
        pil_image = Image.fromstring(
            format, (image.width, image.height), image.get_data(format, pitch))
        try:
            #.convert('P', palette=Image.WEB)
            pil_image.convert("RGB").save(file)
        except Exception, e:
            raise ImageEncodeException(e)


class Interface(object):
    def __init__(self, window):
        self.window = window
    
    def on_mouse_motion(self, x, y, dx, dy):
        if IF_LEFT < x < (self.window.width-IF_RIGHT):
            pass
        else:
            return pyglet.event.EVENT_HANDLED
        if IF_BOTTOM < y < (self.window.height-IF_TOP):
            pass
        else:
            return pyglet.event.EVENT_HANDLED

class LoadScreen(object):
    def __init__(self, window):
        self.window = window
        self.label = pyglet.text.Label('',
                font_name="Linux Libertine",
                font_size=28,
                x=self.window.width-10, y=10,
                anchor_x='right', anchor_y='bottom')
        
        self.label.text = "PARSING MAP FILE..."
        import lib.h3m as h3mlib
        import os
        h3m = h3mlib.extract(os.path.join(pyglet.resource._default_loader._script_home,"maps","A Warm and Familiar Place.h3m"))
        self.label.text = "PARSING MAP FILE..."
        edge_map = [[] for i in xrange(len(h3m["upper_terrain"])+16)]
        for num in xrange(len(edge_map)):
            if num < 7 or num > len(edge_map)-8:
                line = []
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(len(h3m["upper_terrain"][0])+18)])
            elif num == 7:
                line = []
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
                line.append([-1, 16, 0, 0, 0, 0, 0])
                line.extend([[-1, 20+i%4, 0, 0, 0, 0, 0] for i in xrange(len(h3m["upper_terrain"][0]))])
                line.append([-1, 17, 0, 0, 0, 0, 0])
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
            elif num == len(edge_map)-8:
                line = []
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
                line.append([-1, 19, 0, 0, 0, 0, 0])
                line.extend([[-1, 28+i%4, 0, 0, 0, 0, 0] for i in xrange(len(h3m["upper_terrain"][0]))])
                line.append([-1, 18, 0, 0, 0, 0, 0])
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
            else:
                line = []
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
                line.append([-1, 32+num%4, 0, 0, 0, 0, 0])
                line.extend(h3m["upper_terrain"][num-8])
                line.append([-1, 24+num%4, 0, 0, 0, 0, 0])
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
            edge_map[num] = line
        h3m["upper_terrain"] = edge_map
        self.label.text = "INITIATING MAPSET..."
        
        mapset = MapSet(h3m["upper_terrain"], h3m["objects"], h3m["tunedobj"])
        self.label.text = "INITIATING MAPVIEW..."
        mapview = MapView(mapset, self.window)
        interface = Interface(self.window)
        self.window.pop_handlers()
        self.window.push_handlers(mapview)
        self.window.push_handlers(interface)
        self.window.push_handlers(self.window.keys)
        
if __name__ == '__main__':
    window = Window()
    window.push_handlers(LoadScreen(window))
    img = pyglet.resource.image("data/cursors/cradvntr.def/0.png")
    window.set_mouse_cursor(pyglet.window.ImageMouseCursor(img, 0, 40))
    pyglet.app.run()
