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

IF_BOTTOM = 48
IF_RIGHT = 200
IF_TOP = IF_LEFT = 8

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
