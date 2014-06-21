#!/usr/bin/env python

import pyglet

images = [
    pyglet.image.load("puzzle/cas/%d PuzCas%02d.pcx"%(i+2745, i)) for i in xrange(20)
]

bin = pyglet.image.atlas.TextureBin()
images = [bin.add(image) for image in images]

window = pyglet.window.Window(800,600)
image = pyglet.resource.image('interface/3178 Puzzle.pcx')
image1 = pyglet.resource.image('interface/153 AResBar.pcx')

@window.event
def on_draw():
    window.clear()
    image.blit(0, 0)
    image1.blit(3, 3)
    images[0].blit(7,414)
    images[1].blit(7,402)
    images[2].blit(7,412)
    images[3].blit(7,359)
    images[4].blit(7,264)
    images[5].blit(7,49)
    images[6].blit(16,527)
    images[7].blit(22,49)
    images[8].blit(70,49)
    images[9].blit(72,285)

@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.Q:
        pyglet.app.exit()

pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
 
pyglet.app.run()
