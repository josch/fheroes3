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
            pyglet.image.get_buffer_manager().get_color_buffer().save(
                'screenshot.png', encoder=PNGRGBEncoder())

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
