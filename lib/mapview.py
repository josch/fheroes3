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
from lib.interface import *
from lib.mapset import *

class MapView(object):
    def __init__(self, mapset, window):
        self.window = window
        self.mapset = mapset
        self._first_time_init()
        self._init_view()
        # mouse position
        self.label = pyglet.text.Label('',
                font_name="",
                font_size=36,
                bold=True,
                color=(128, 128, 128, 128),
                x=self.window.width - 10, y=0,
                anchor_x='right', anchor_y='bottom')
        self.animate = True
        pyglet.clock.schedule_interval(self.animate_water, 1/6.0)
        pyglet.clock.schedule_interval(self.update, 1/60.0)
    
    def _first_time_init(self):
        self.tile_size = 32
        # size of the viewport
        self.vp_width = self.window.width-IF_RIGHT-IF_LEFT
        self.vp_height = self.window.height-IF_BOTTOM-IF_TOP
        # center map
        self.x = (self.mapset.width * self.tile_size - self.vp_width + 
                  self.tile_size) // 2
        self.y = (self.mapset.height * self.tile_size - self.vp_height + 
                  self.tile_size) // 2
        self.mouse_x = self.mouse_dx = 0
        self.mouse_y = self.mouse_dy = 0
    
    def _init_view(self):
        # initiate new batch
        self.batch = pyglet.graphics.Batch()
        # initiate new vertex list
        self.vl_objects = [None for value in self.mapset.groups]
        # size of the viewport
        self.vp_width = self.window.width - IF_RIGHT - IF_LEFT
        self.vp_height = self.window.height - IF_BOTTOM - IF_TOP
        # center map when viewport is too large, else check if map still fills
        # whole viewport and if not adjust position accordingly
        self.center_x = False
        if self.mapset.width * self.tile_size < self.vp_width:
            # center the map in x direction
            self.center_x = True
            self.x = (self.mapset.width * self.tile_size - self.vp_width) // 2
        elif self.x > self.tile_size * self.mapset.width - self.vp_width:
            # move map back to the right
            self.x = self.tile_size * self.mapset.width - self.vp_width
        elif self.x < 0:
            # move map to the left
            self.x = 0
        self.center_y = False
        if self.mapset.height * self.tile_size < self.vp_height:
            # center the map in y direction
            self.center_y = True
            self.y = (self.mapset.height * self.tile_size -
                      self.vp_height) // 2
        elif self.y > self.tile_size * self.mapset.height - self.vp_height:
            # move map up
            self.y = self.tile_size * self.mapset.height - self.vp_height
        elif self.y < 0:
            # move map down
            self.y = 0
        # tiles to be drawn with the current viewport size
        self.tiles_x = min((self.vp_width // self.tile_size) + 2,
                           self.mapset.width)
        self.tiles_y = min((self.vp_height // self.tile_size) + 2,
                           self.mapset.height)
        # undrawn map size in pixels
        self.undrawn_x = self.tile_size * (self.mapset.width - self.tiles_x)
        self.undrawn_y = self.tile_size * (self.mapset.height - self.tiles_y)
        # reset mouse or keyboard movement
        self.dx = 0
        self.dy = 0
        # calculate modulo pixel position of the map
        if self.x - self.tile_size > self.undrawn_x:
            # dont go right beyond map borders
            mod_x = self.tile_size - self.x + self.undrawn_x
        elif self.x > 0:
            # calculate modulo of current position and tile_size
            mod_x = (self.tile_size - self.x) % self.tile_size
        else:
            # dont go left beyond map borders
            mod_x = self.tile_size - self.x
        if self.y - self.tile_size > self.undrawn_y:
            # dont go up beyond map borders
            mod_y = self.tile_size - self.y + self.undrawn_y
        elif self.y > 0:
            # calculate modulo of current position and tile_size
            mod_y = (self.tile_size - self.y) % self.tile_size
        else:
            # dont go down beyond map borders
            mod_y = self.tile_size - self.y
        # calculate tile position of the map, turn y coordinates upside down
        self.div_x = (self.tile_size - self.x - mod_x) // self.tile_size
        self.div_y = (self.tile_size - self.y - mod_y) // self.tile_size + \
                     self.mapset.height - 1
        # update vertex lists with the gathered information
        self.update_vertex_lists()
        # update current current position that is to be glTranslated
        # XXX: dont ask me why i have to add 1/4 and 3/2 but when i do not
        #      there are black borders when zooming out
        #      plz explain wtf is going on there
        self.view_x = mod_x - self.tile_size - (self.tile_size - 32) // 4
        self.view_y = mod_y - self.tile_size - ((self.tile_size - 32) * 3) // 2
    
    def draw(self):
        pyglet.gl.glTranslatef(self.view_x+IF_LEFT, self.view_y+IF_BOTTOM, 0)
        pyglet.gl.glScalef(self.tile_size/32.0, self.tile_size/32.0, 0.0)
        pyglet.gl.glEnable(pyglet.gl.GL_TEXTURE_2D)
        self.batch.draw()
        pyglet.gl.glDisable(pyglet.gl.GL_TEXTURE_2D)
    
    def _move(self, dx, dy):
        # new map position
        new_x = self.x - dx
        new_y = self.y - dy
        # only update textures and vertices when necessary
        retex = False
        # if x or y jump is too big, adjust new position accordingly
        if new_x < 0:
            # move map to the left
            new_x = 0
            retex = True
        if new_x > self.tile_size * self.mapset.width - self.vp_width:
            # move map to the right
            new_x = self.tile_size * self.mapset.width - self.vp_width
            retex = True
        if new_y < 0:
            # move map down
            new_y = 0
            retex = True
        if new_y > self.tile_size * self.mapset.height - self.vp_height:
            # move map up
            new_y = self.tile_size * self.mapset.height - self.vp_height
            retex = True
        # find out how many steps and pixels we have to move and wether we have
        # to retex
        if new_x - self.tile_size > self.undrawn_x:
            # we are at the right border
            mod_x = self.tile_size - new_x + self.undrawn_x
            # only retex if the last position was not at the border
            if self.x - self.tile_size <= self.undrawn_x:
                retex = True
        elif new_x > 0:
            # normal movement: calculate the amount of steps and the modulo
            div_x, mod_x = divmod(self.tile_size - new_x, self.tile_size)
            # only retex if the number of moved steps is not equal to last
            if div_x != (self.tile_size - self.x) // self.tile_size:
                retex = True
        else:
            # we are at the left border
            mod_x = self.tile_size - new_x
        if new_y - self.tile_size > self.undrawn_y:
            # we are at the top
            mod_y = self.tile_size - new_y + self.undrawn_y
            # only retex if the last position was not at the border
            if self.y - self.tile_size <= self.undrawn_y:
                retex = True
        elif new_y > 0:
            # normal movement: calculate the amount of steps and the modulo
            div_y, mod_y = divmod(self.tile_size - new_y, self.tile_size)
            # only retex if the number of moved steps is not equal to last
            if div_y != (self.tile_size - self.y) // self.tile_size:
                retex = True
        else:
            # we are at the bottom
            mod_y = self.tile_size - new_y
        # if we have to update vertices and textures
        if retex:
            # calculate the current position on the tilemap
            self.div_x = (self.tile_size - new_x - mod_x) // \
                         self.tile_size
            self.div_y = (self.tile_size - new_y - mod_y) // \
                         self.tile_size + self.mapset.height - 1
            self.update_vertex_lists()
        # update position if not centered
        # XXX: dont ask me why i have to add 1/4 and 3/2 but when i do not
        #      there are black borders when zooming out
        #      plz explain wtf is going on there
        if not self.center_x:
            self.view_x = mod_x-self.tile_size-(self.tile_size-32)//4
            self.x = new_x
        if not self.center_y:
            self.view_y = mod_y-self.tile_size-((self.tile_size-32)*3)//2
            self.y = new_y
    
    def update_vertex_lists(self):
        # initiate lists of vertex lists, vertices, texture coords, vertices
        # counts and map objects for each group
        vertices = [[] for value in self.mapset.groups]
        tex_coords = [[] for value in self.mapset.groups]
        count = [0 for value in self.mapset.groups]
        self.cur_objects = [[] for value in self.mapset.atlases]
        # for each tile in the viewport, update the list of the specific group
        for obj, coords in self.mapset.get_tiles(self.tiles_x, self.tiles_y,
                                                 self.div_x, self.div_y):
            tex_coords[obj.group].extend(obj.tex_coords)
            vertices[obj.group].extend(coords)
            count[obj.group]+=4
            if isinstance(obj, Animation_Object) and len(obj.animation) > 1:
                self.cur_objects[obj.animation.atlas].append(obj.animation)
        for i, group in enumerate(self.mapset.groups):
            if count[i] == 0:
                if self.vl_objects[i] is None:
                    # let the vertex list be None
                    pass
                else:
                    # there was a vertex list but now no more - delete it
                    self.vl_objects[i].delete()
                    self.vl_objects[i] = None
            else:
                if self.vl_objects[i] is None:
                    # there was no vertex list but ther now is one - create it
                    self.vl_objects[i] = self.batch.add(count[i],
                            pyglet.gl.GL_QUADS,
                            group,
                            ('v2i', vertices[i]),
                            ('t3f', tex_coords[i]),
                            ('c4B', (255,255,255,255)*count[i]))
                else:
                    # there already is a vertex list - resize and refill
                    self.vl_objects[i].resize(count[i])
                    self.vl_objects[i].tex_coords = tex_coords[i]
                    self.vl_objects[i].vertices = vertices[i]
                    self.vl_objects[i].colors = (255,255,255,255)*count[i]
        # make object list unique
        for i, atlas in enumerate(self.mapset.atlases):
            self.cur_objects[i] = list(set(self.cur_objects[i]))
    
    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.PLUS and self.tile_size < 32:
            self.tile_size+=8
            self._init_view()
        elif symbol == pyglet.window.key.MINUS and self.tile_size > 16:
            self.tile_size-=8
            self._init_view()
        elif symbol == pyglet.window.key.A:
            if self.animate:
                pyglet.clock.unschedule(self.animate_water)
                self.animate = False
            else:
                pyglet.clock.schedule_interval(self.animate_water, 1/6.0)
                self.animate = True
    
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
        except KeyError:
            pass
        if self.dx or self.dy:
            self._move(self.dx, self.dy)
            self.dx = 0
            self.dy = 0
        # mouse position:
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
        for i, atlas in enumerate(self.mapset.atlases):
            if len(self.cur_objects[i]) > 0:
                pyglet.gl.glBindTexture(atlas.texture.target, atlas.texture.id)
                for obj in self.cur_objects[i]:
                    pyglet.gl.glTexSubImage2D(obj.tex.owner.target,
                            obj.tex.owner.level,
                            obj.tex.x, obj.tex.y,
                            obj.tex.width, obj.tex.height,
                            pyglet.gl.GL_RGBA, pyglet.gl.GL_UNSIGNED_BYTE,
                            obj.next_frame())
