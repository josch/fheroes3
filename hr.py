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
from lib.mapset import *
from lib.interface import *
from lib.mapview import *
from lib.render import *
from lib.window import Window
import sys

class LoadScreen(object):
    def __init__(self, window, map_name):
        self.window = window
        self.label = pyglet.text.Label('',
                font_name="Linux Libertine",
                font_size=28,
                x=self.window.width-10, y=10,
                anchor_x='right', anchor_y='bottom')
        self.label.text = "INITIATING MAPSET..."
        mapset = MapSet(map_name)
        self.label.text = "INITIATING MAPVIEW..."
        mapview = MapView(mapset, self.window)
        interface = Interface(self.window)
        renderer = Renderer(self.window, mapview, interface)
        self.window.pop_handlers()
        self.window.push_handlers(renderer)
        self.window.push_handlers(mapview)
        self.window.push_handlers(interface)
        
if __name__ == '__main__':
    pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA,
        pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
    window = Window(width=1024, height=768)
    if len(sys.argv) < 2:
        sys.exit("specify the map you want to load from the map folder\nusage: python hr.py \"A Viking We Shall Go\"")
    
    if not os.path.exists(os.path.join(pyglet.resource._default_loader._script_home,"maps","%s.h3m" % sys.argv[1])):
        sys.exit("cannot find file %s" % os.path.join(pyglet.resource._default_loader._script_home,"maps","%s.h3m" % sys.argv[1]))
    window.push_handlers(LoadScreen(window, sys.argv[1]))
    img = pyglet.resource.image("data/cursors/cradvntr.def/0.png")
    window.set_mouse_cursor(pyglet.window.ImageMouseCursor(img, 0, 40))
    pyglet.app.run()
