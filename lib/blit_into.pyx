cdef extern from "include_gl.h":
    ctypedef unsigned int GLenum
    ctypedef int GLint
    ctypedef unsigned int GLuint
    ctypedef int GLsizei
    ctypedef void GLvoid
    
    cdef int GL_RGBA
    cdef int GL_UNSIGNED_BYTE
    
    cdef void glTexSubImage2D(GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLenum type, char *pixels)
    cdef void glBindTexture(GLenum target, GLuint texture)

def render(atlases, objects):
    cdef char *data
    for i, atlas in enumerate(atlases):
        if len(objects[i]) > 0:
            glBindTexture(atlas.texture.target, atlas.texture.id)
            for obj in objects[i]:
                temp = obj.next_frame()
                data = temp
                tex = obj.tex
                glTexSubImage2D(tex.owner.target,
                        tex.owner.level,
                        tex.x, tex.y,
                        tex.width, tex.height,
                        GL_RGBA, GL_UNSIGNED_BYTE,
                        data)
