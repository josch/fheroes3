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

class Renderer(object):
    def __init__(self, window, mapview, interface):
        self.window = window
        self.mapview = mapview
        self.interface = interface

    def on_draw(self):
        pyglet.gl.glClear(pyglet.gl.GL_COLOR_BUFFER_BIT)
        pyglet.gl.glPushMatrix()
        self.mapview.draw()
        pyglet.gl.glPopMatrix()
        pyglet.gl.glLoadIdentity()
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        self.interface.draw()
        self.window.draw()
        return pyglet.event.EVENT_HANDLED
