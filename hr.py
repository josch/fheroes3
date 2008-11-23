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
from lib.window import Window

class LoadScreen(object):
    def __init__(self, window):
        self.window = window
        self.label = pyglet.text.Label('',
                font_name="Linux Libertine",
                font_size=28,
                x=self.window.width-10, y=10,
                anchor_x='right', anchor_y='bottom')
        self.label.text = "INITIATING MAPSET..."
        mapset = MapSet("Deluge")
        self.label.text = "INITIATING MAPVIEW..."
        mapview = MapView(mapset, self.window)
        interface = Interface(self.window)
        self.window.pop_handlers()
        self.window.push_handlers(mapview)
        self.window.push_handlers(interface)
        self.window.push_handlers(self.window.keys)
        
if __name__ == '__main__':
    pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA,
        pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
    window = Window()
    window.push_handlers(LoadScreen(window))
    img = pyglet.resource.image("data/cursors/cradvntr.def/0.png")
    window.set_mouse_cursor(pyglet.window.ImageMouseCursor(img, 0, 40))
    pyglet.app.run()
