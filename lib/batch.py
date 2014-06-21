###############################################################################
##                                  __init__.py                              ##
###############################################################################

import ctypes

import pyglet
from pyglet.gl import *
import ctypes
import re

_debug_graphics_batch = pyglet.options['debug_graphics_batch']

def _parse_data(data):
    '''Given a list of data items, returns (formats, initial_arrays).'''
    assert data, 'No attribute formats given'

    # Return tuple (formats, initial_arrays).
    formats = []
    initial_arrays = []
    for i, format in enumerate(data):
        if isinstance(format, tuple):
            format, array = format
            initial_arrays.append((i, array))
        formats.append(format)
    formats = tuple(formats)
    return formats, initial_arrays

def _get_default_batch():
    shared_object_space = gl.current_context.object_space
    try:
        return shared_object_space.pyglet_graphics_default_batch
    except AttributeError:
        shared_object_space.pyglet_graphics_default_batch = Batch()
        return shared_object_space.pyglet_graphics_default_batch

def vertex_list(count, *data):
    '''Create a `VertexList` not associated with a batch, group or mode.

    :Parameters:
        `count` : int
            The number of vertices in the list.
        `data` : data items
            Attribute formats and initial data for the vertex list.  See the
            module summary for details.

    :rtype: `VertexList`
    '''
    # Note that mode=0 because the default batch is never drawn: vertex lists
    # returned from this function are drawn directly by the app.
    return _get_default_batch().add(count, 0, None, *data)

class DomainDraw(object):
    def __init__(self, domain, mode, group):
        self.domain = domain
        self.mode = mode
        self.group = group
    
    def draw(self):
        self.group.set_state()
        self.domain.draw(self.mode)
        self.group.unset_state()

class Batch(object):
    '''Manage a collection of vertex lists for batched rendering.

    Vertex lists are added to a `Batch` using the `add` and `add_indexed`
    methods.  An optional group can be specified along with the vertex list,
    which gives the OpenGL state required for its rendering.  Vertex lists
    with shared mode and group are allocated into adjacent areas of memory and
    sent to the graphics card in a single operation.

    Call `VertexList.delete` to remove a vertex list from the batch.
    '''
    def __init__(self):
        '''Create a graphics batch.'''
        # Mapping to find domain.  
        # group -> (attributes, mode, indexed) -> domain
        self.group_map = {}

        # Mapping of group to list of children.
        self.group_children = {}

        # List of top-level groups
        self.top_groups = []

        self._draw_list = []
        self._draw_list_dirty = False

    def add(self, count, mode, group, *data):
        '''Add a vertex list to the batch.

        :Parameters:
            `count` : int
                The number of vertices in the list.
            `mode` : int
                OpenGL drawing mode enumeration; for example, one of
                ``GL_POINTS``, ``GL_LINES``, ``GL_TRIANGLES``, etc.
                See the module summary for additional information.
            `group` : `Group`
                Group of the vertex list, or ``None`` if no group is required.
            `data` : data items
                Attribute formats and initial data for the vertex list.  See
                the module summary for details.

        :rtype: `VertexList`
        '''
        formats, initial_arrays = _parse_data(data)
        domain = self._get_domain(False, mode, group, formats)
        domain.__formats = formats
            
        # Create vertex list and initialize
        vlist = domain.create(count)
        for i, array in initial_arrays:
            vlist._set_attribute_data(i, array)

        return vlist

    def _get_domain(self, indexed, mode, group, formats):
        if group is None:
            group = null_group
        
        # Batch group
        if group not in self.group_map:
            self._add_group(group)

        domain_map = self.group_map[group]

        # Find domain given formats, indices and mode
        key = (formats, mode, indexed)
        try:
            domain = domain_map[key]
        except KeyError:
            # Create domain
            if indexed:
                domain = vertexdomain.create_indexed_domain(*formats)
            else:
                domain = create_domain(*formats)
            domain_map[key] = domain
            self._draw_list_dirty = True 

        return domain

    def _add_group(self, group):
        self.group_map[group] = {}
        if group.parent is None:
            self.top_groups.append(group)
        else:
            if group.parent not in self.group_map:
                self._add_group(group.parent)
            if group.parent not in self.group_children:
                self.group_children[group.parent] = []
            self.group_children[group.parent].append(group)
        self._draw_list_dirty = True

    def visit(self, group):
        draw_list = []

        # Draw domains using this group
        domain_map = self.group_map[group]
        for (formats, mode, indexed), domain in list(domain_map.items()):
            # Remove unused domains from batch
            if domain._is_empty():
                del domain_map[(formats, mode, indexed)]
                continue
            draw_list.append(DomainDraw(domain, mode, group))

        # Sort and visit child groups of this group
        children = self.group_children.get(group)
        if children:
            children.sort()
            for child in list(children):
                draw_list.extend(visit(child))

        if children or domain_map:
            return draw_list
        else:
            # Remove unused group from batch
            del self.group_map[group]
            if group.parent:
                self.group_children[group.parent].remove(group)
            try:
                del self.group_children[group]
            except KeyError:
                pass
            try:
                self.top_groups.remove(group)
            except ValueError:
                pass
            return []
    
    def _update_draw_list(self):
        '''Visit group tree in preorder and create a list of bound methods
        to call.
        '''

        self._draw_list = []

        self.top_groups.sort()
        for group in list(self.top_groups):
            self._draw_list.extend(self.visit(group))

        self._draw_list_dirty = False

        if _debug_graphics_batch:
            self._dump_draw_list()
        
    def draw(self):
        '''Draw the batch.
        '''
        if self._draw_list_dirty:
            self._update_draw_list()

        for func in self._draw_list:
            func.draw()

class Group(object):
    '''Group of common OpenGL state.

    Before a vertex list is rendered, its group's OpenGL state is set; as are
    that state's ancestors' states.  This can be defined arbitrarily on
    subclasses; the default state change has no effect, and groups vertex
    lists only in the order in which they are drawn.
    '''
    def __init__(self, parent=None):
        '''Create a group.

        :Parameters:
            `parent` : `Group`
                Group to contain this group; its state will be set before this
                state's.

        '''
        self.parent = parent

    def set_state(self):
        '''Apply the OpenGL state change.  
        
        The default implementation does nothing.'''
        pass

    def unset_state(self):
        '''Repeal the OpenGL state change.
        
        The default implementation does nothing.'''
        pass

    def set_state_recursive(self):
        '''Set this group and its ancestry.

        Call this method if you are using a group in isolation: the
        parent groups will be called in top-down order, with this class's
        `set` being called last.
        '''
        if self.parent:
            self.parent.set_state_recursive()
        self.set_state()

    def unset_state_recursive(self):
        '''Unset this group and its ancestry.

        The inverse of `set_state_recursive`.
        '''
        self.unset_state()
        if self.parent:
            self.parent.unset_state_recursive()

class NullGroup(Group):
    '''The default group class used when ``None`` is given to a batch.

    This implementation has no effect.
    '''
    pass

#: The default group.
#:
#: :type: `Group`
null_group = NullGroup()


###############################################################################
##                                allocation.py                              ##
###############################################################################

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'
 
# Common cases:
# -regions will be the same size (instances of same object, e.g. sprites)
# -regions will not usually be resized (only exception is text)
# -alignment of 4 vertices (glyphs, sprites, images, ...)
#
# Optimise for:
# -keeping regions adjacent, reduce the number of entries in glMultiDrawArrays
# -finding large blocks of allocated regions quickly (for drawing)
# -finding block of unallocated space is the _uncommon_ case!
#
# Decisions:
# -don't over-allocate regions to any alignment -- this would require more
#  work in finding the allocated spaces (for drawing) and would result in
#  more entries in glMultiDrawArrays
# -don't move blocks when they truncate themselves.  try not to allocate the
#  space they freed too soon (they will likely need grow back into it later,
#  and growing will usually require a reallocation).
# -allocator does not track individual allocated regions.  Trusts caller
#  to provide accurate (start, size) tuple, which completely describes
#  a region from the allocator's point of view.
# -this means that compacting is probably not feasible, or would be hideously
#  expensive

class AllocatorMemoryException(Exception):
    '''The buffer is not large enough to fulfil an allocation.

    Raised by `Allocator` methods when the operation failed due to lack of
    buffer space.  The buffer should be increased to at least
    requested_capacity and then the operation retried (guaranteed to
    pass second time).
    '''

    def __init__(self, requested_capacity):
        self.requested_capacity = requested_capacity

class Allocator(object):
    '''Buffer space allocation implementation.'''
    def __init__(self, capacity):
        '''Create an allocator for a buffer of the specified capacity.

        :Parameters:
            `capacity` : int
                Maximum size of the buffer.

        '''
        self.capacity = capacity

        # Allocated blocks.  Start index and size in parallel lists.
        #
        # # = allocated, - = free
        #
        #  0  3 5        15   20  24                    40
        # |###--##########-----####----------------------|
        #
        # starts = [0, 5, 20]
        # sizes = [3, 10, 4]
        #
        # To calculate free blocks:
        # for i in range(0, len(starts)):
        #   free_start[i] = starts[i] + sizes[i]
        #   free_size[i] =  starts[i+1] - free_start[i]
        # free_size[i+1] = self.capacity - free_start[-1]

        self.starts = []
        self.sizes = []

    def set_capacity(self, size):
        '''Resize the maximum buffer size.
        
        The capaity cannot be reduced.

        :Parameters:
            `size` : int
                New maximum size of the buffer.

        '''
        assert size > self.capacity
        self.capacity = size

    def alloc(self, size):
        '''Allocate memory in the buffer.

        Raises `AllocatorMemoryException` if the allocation cannot be
        fulfilled.

        :Parameters:
            `size` : int
                Size of region to allocate.
               
        :rtype: int
        :return: Starting index of the allocated region.
        '''
        assert size > 0

        # return start
        # or raise AllocatorMemoryException

        if not self.starts:
            if size <= self.capacity:
                self.starts.append(0)
                self.sizes.append(size)
                return 0
            else:
                raise AllocatorMemoryException(size)

        # Allocate in a free space
        free_start = self.starts[0] + self.sizes[0]
        for i, (alloc_start, alloc_size) in \
                enumerate(zip(self.starts[1:], self.sizes[1:])):
            # Danger!  
            # i is actually index - 1 because of slicing above...
            # starts[i]   points to the block before this free space
            # starts[i+1] points to the block after this free space, and is
            #             always valid.
            free_size = alloc_start - free_start
            if free_size == size:
                # Merge previous block with this one (removing this free space)
                self.sizes[i] += free_size + alloc_size
                del self.starts[i+1]
                del self.sizes[i+1]
                return free_start
            elif free_size > size:
                # Increase size of previous block to intrude into this free
                # space.
                self.sizes[i] += size
                return free_start
            free_start = alloc_start + alloc_size
        
        # Allocate at end of capacity
        free_size = self.capacity - free_start
        if free_size >= size:
            self.sizes[-1] += size
            return free_start
        
        raise AllocatorMemoryException(self.capacity + size - free_size)

    def realloc(self, start, size, new_size):
        '''Reallocate a region of the buffer.

        This is more efficient than separate `dealloc` and `alloc` calls, as
        the region can often be resized in-place.

        Raises `AllocatorMemoryException` if the allocation cannot be
        fulfilled.

        :Parameters:
            `start` : int
                Current starting index of the region.
            `size` : int
                Current size of the region.
            `new_size` : int
                New size of the region.

        '''
        assert size > 0 and new_size > 0
        
        # return start
        # or raise AllocatorMemoryException

        # Truncation is the same as deallocating the tail cruft
        if new_size < size:
            self.dealloc(start + new_size, size - new_size)
            return start
            
        # Find which block it lives in
        for i, (alloc_start, alloc_size) in \
                enumerate(zip(*(self.starts, self.sizes))):
            p = start - alloc_start
            if p >= 0 and size <= alloc_size - p:
                break
        if not (p >= 0 and size <= alloc_size - p):
            print zip(self.starts, self.sizes)
            print start, size, new_size
            print p, alloc_start, alloc_size
        assert p >= 0 and size <= alloc_size - p, 'Region not allocated'

        if size == alloc_size - p:
            # Region is at end of block.  Find how much free space is after
            # it.
            is_final_block = i == len(self.starts) - 1
            if not is_final_block:
                free_size = self.starts[i + 1] - (start + size)
            else:
                free_size = self.capacity - (start + size)

            # TODO If region is an entire block being an island in free space, 
            # can possibly extend in both directions.

            if free_size == new_size - size and not is_final_block:
                # Merge block with next (region is expanded in place to
                # exactly fill the free space)
                self.sizes[i] += free_size + self.sizes[i + 1]
                del self.starts[i + 1]
                del self.sizes[i + 1]
                return start
            elif free_size > new_size - size:
                # Expand region in place
                self.sizes[i] += new_size - size
                return start

        # The block must be repositioned.  Dealloc then alloc.
        
        # But don't do this!  If alloc fails, we've already silently dealloc'd
        # the original block.
        #   self.dealloc(start, size)
        #   return self.alloc(new_size)

        # It must be alloc'd first.  We're not missing an optimisation 
        # here, because if freeing the block would've allowed for the block to 
        # be placed in the resulting free space, one of the above in-place
        # checks would've found it.
        result = self.alloc(new_size)
        self.dealloc(start, size)
        return result

    def dealloc(self, start, size):
        '''Free a region of the buffer.

        :Parameters:
            `start` : int
                Starting index of the region.
            `size` : int
                Size of the region.

        '''
        assert size > 0
        assert self.starts
        
        # Find which block needs to be split
        for i, (alloc_start, alloc_size) in \
                enumerate(zip(*(self.starts, self.sizes))):
            p = start - alloc_start
            if p >= 0 and size <= alloc_size - p:
                break
        
        # Assert we left via the break
        assert p >= 0 and size <= alloc_size - p, 'Region not allocated'

        if p == 0 and size == alloc_size:
            # Remove entire block
            del self.starts[i]
            del self.sizes[i]
        elif p == 0:
            # Truncate beginning of block
            self.starts[i] += size
            self.sizes[i] -= size
        elif size == alloc_size - p:
            # Truncate end of block
            self.sizes[i] -= size
        else:
            # Reduce size of left side, insert block at right side
            #   $ = dealloc'd block, # = alloc'd region from same block
            #
            #   <------8------>
            #   <-5-><-6-><-7->
            #   1    2    3    4
            #   #####$$$$$#####
            #
            #   1 = alloc_start
            #   2 = start
            #   3 = start + size
            #   4 = alloc_start + alloc_size
            #   5 = start - alloc_start = p
            #   6 = size
            #   7 = {8} - ({5} + {6}) = alloc_size - (p + size)
            #   8 = alloc_size
            #
            self.sizes[i] = p
            self.starts.insert(i + 1, start + size)
            self.sizes.insert(i + 1, alloc_size - (p + size))

    def get_allocated_regions(self):
        '''Get a list of (aggregate) allocated regions.

        The result of this method is ``(starts, sizes)``, where ``starts`` is
        a list of starting indices of the regions and ``sizes`` their
        corresponding lengths.

        :rtype: (list, list)
        '''
        # return (starts, sizes); len(starts) == len(sizes)
        return (self.starts, self.sizes)

    def get_fragmented_free_size(self):
        '''Returns the amount of space unused, not including the final
        free block.

        :rtype: int
        '''
        if not self.starts:
            return 0

        # Variation of search for free block.
        total_free = 0
        free_start = self.starts[0] + self.sizes[0]
        for i, (alloc_start, alloc_size) in \
                enumerate(zip(self.starts[1:], self.sizes[1:])):
            total_free += alloc_start - free_start
            free_start = alloc_start + alloc_size

        return total_free

    def get_free_size(self):
        '''Return the amount of space unused.
        
        :rtype: int
        '''
        if not self.starts:
            return self.capacity

        free_end = self.capacity - (self.starts[-1] + self.sizes[-1])
        return self.get_fragmented_free_size() + free_end

    def get_usage(self):
        '''Return fraction of capacity currently allocated.
        
        :rtype: float
        '''
        return 1. - self.get_free_size() / float(self.capacity)

    def get_fragmentation(self):
        '''Return fraction of free space that is not expandable.
        
        :rtype: float
        '''
        free_size = self.get_free_size()
        if free_size == 0:
            return 0.
        return self.get_fragmented_free_size() / float(self.get_free_size())

    def _is_empty(self):
        return not self.starts

    def __str__(self):
        return 'allocs=' + repr(zip(self.starts, self.sizes))

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, str(self))


###############################################################################
##                           vertexattribute.py                              ##
###############################################################################

_c_types = {
    GL_BYTE: ctypes.c_byte,
    GL_UNSIGNED_BYTE: ctypes.c_ubyte,
    GL_SHORT: ctypes.c_short,
    GL_UNSIGNED_SHORT: ctypes.c_ushort,
    GL_INT: ctypes.c_int,
    GL_UNSIGNED_INT: ctypes.c_uint,
    GL_FLOAT: ctypes.c_float,
    GL_DOUBLE: ctypes.c_double,
}

_gl_types = {
    'b': GL_BYTE,
    'B': GL_UNSIGNED_BYTE,
    's': GL_SHORT,
    'S': GL_UNSIGNED_SHORT,
    'i': GL_INT,
    'I': GL_UNSIGNED_INT,
    'f': GL_FLOAT,
    'd': GL_DOUBLE,
}

_attribute_format_re = re.compile(r'''
    (?P<name>
       [cefnstv] | 
       (?P<generic_index>[0-9]+) g
       (?P<generic_normalized>n?))
    (?P<count>[1234])
    (?P<type>[bBsSiIfd])
''', re.VERBOSE)

_attribute_cache = {}

def create_attribute(format):
    '''Create a vertex attribute description from a format string.
    
    The initial stride and offset of the attribute will be 0.

    :Parameters:
        `format` : str
            Attribute format string.  See the module summary for details.

    :rtype: `AbstractAttribute`
    '''
    try:
        cls, args = _attribute_cache[format]
        return cls(*args)
    except KeyError:
        pass

    match = _attribute_format_re.match(format)
    assert match, 'Invalid attribute format %r' % format
    count = int(match.group('count'))
    gl_type = _gl_types[match.group('type')]
    generic_index = match.group('generic_index')
    if generic_index:
        normalized = match.group('generic_normalized')
        attr_class = GenericAttribute
        args = int(generic_index), normalized, count, gl_type
    else:
        name = match.group('name')
        attr_class = _attribute_classes[name]
        if attr_class._fixed_count:
            assert count == attr_class._fixed_count, \
                'Attributes named "%s" must have count of %d' % (
                    name, attr_class._fixed_count)
            args = (gl_type,)
        else:
            args = (count, gl_type)
    
    _attribute_cache[format] = attr_class, args
    return attr_class(*args)

class AbstractAttribute(object):
    '''Abstract accessor for an attribute in a mapped buffer.
    '''
    
    _fixed_count = None
    
    def __init__(self, count, gl_type):
        '''Create the attribute accessor.

        :Parameters:
            `count` : int
                Number of components in the attribute.
            `gl_type` : int
                OpenGL type enumerant; for example, ``GL_FLOAT``

        '''
        assert count in (1, 2, 3, 4), 'Component count out of range'
        self.gl_type = gl_type
        self.c_type = _c_types[gl_type]
        self.count = count
        self.align = ctypes.sizeof(self.c_type)
        self.size = count * self.align
        self.stride = self.size
        self.offset = 0

    def enable(self):
        '''Enable the attribute using ``glEnableClientState``.'''
        raise NotImplementedError('abstract')

    def set_pointer(self, offset):
        '''Setup this attribute to point to the currently bound buffer at
        the given offset.

        ``offset`` should be based on the currently bound buffer's ``ptr``
        member.

        :Parameters:
            `offset` : int
                Pointer offset to the currently bound buffer for this
                attribute.

        '''
        raise NotImplementedError('abstract')

    def get_region(self, buffer, start, count):
        '''Map a buffer region using this attribute as an accessor.

        The returned region can be modified as if the buffer was a contiguous
        array of this attribute (though it may actually be interleaved or
        otherwise non-contiguous).

        The returned region consists of a contiguous array of component
        data elements.  For example, if this attribute uses 3 floats per
        vertex, and the `count` parameter is 4, the number of floats mapped
        will be ``3 * 4 = 12``.

        :Parameters:
            `buffer` : `AbstractMappable`
                The buffer to map.
            `start` : int
                Offset of the first vertex to map.
            `count` : int
                Number of vertices to map

        :rtype: `AbstractBufferRegion`
        '''
        byte_start = self.stride * start
        byte_size = self.stride * count
        array_count = self.count * count
        if self.stride == self.size:
            # non-interleaved
            ptr_type = ctypes.POINTER(self.c_type * array_count)
            return buffer.get_region(byte_start, byte_size, ptr_type)
        else:
            # interleaved
            byte_start += self.offset
            byte_size -= self.offset
            elem_stride = self.stride // ctypes.sizeof(self.c_type)
            elem_offset = self.offset // ctypes.sizeof(self.c_type)
            ptr_type = ctypes.POINTER(
                self.c_type * (count * elem_stride - elem_offset))
            region = buffer.get_region(byte_start, byte_size, ptr_type)
            return vertexbuffer.IndirectArrayRegion(
                region, array_count, self.count, elem_stride)

    def set_region(self, buffer, start, count, data):
        '''Set the data over a region of the buffer.

        :Parameters:
            `buffer` : AbstractMappable`
                The buffer to modify.
            `start` : int
                Offset of the first vertex to set.
            `count` : int
                Number of vertices to set.
            `data` : sequence
                Sequence of data components.

        '''
        if self.stride == self.size:
            # non-interleaved
            byte_start = self.stride * start
            byte_size = self.stride * count
            array_count = self.count * count
            data = (self.c_type * array_count)(*data)
            buffer.set_data_region(data, byte_start, byte_size)
        else:
            # interleaved
            region = self.get_region(buffer, start, count)
            region[:] = data

class ColorAttribute(AbstractAttribute):
    '''Color vertex attribute.'''

    plural = 'colors'
    
    def __init__(self, count, gl_type):
        assert count in (3, 4), 'Color attributes must have count of 3 or 4'
        super(ColorAttribute, self).__init__(count, gl_type)

    def enable(self):
        glEnableClientState(GL_COLOR_ARRAY)
    
    def set_pointer(self, pointer):
        glColorPointer(self.count, self.gl_type, self.stride,
                       self.offset + pointer)

class TexCoordAttribute(AbstractAttribute):
    '''Texture coordinate attribute.'''

    plural = 'tex_coords'

    def __init__(self, count, gl_type):
        assert gl_type in (GL_SHORT, GL_INT, GL_INT, GL_FLOAT, GL_DOUBLE), \
            'Texture coord attribute must have non-byte signed type'
        super(TexCoordAttribute, self).__init__(count, gl_type)

    def enable(self):
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
    
    def set_pointer(self, pointer):
        glTexCoordPointer(self.count, self.gl_type, self.stride,
                       self.offset + pointer)

class VertexAttribute(AbstractAttribute):
    '''Vertex coordinate attribute.'''

    plural = 'vertices'

    def __init__(self, count, gl_type):
        assert count > 1, \
            'Vertex attribute must have count of 2, 3 or 4'
        assert gl_type in (GL_SHORT, GL_INT, GL_INT, GL_FLOAT, GL_DOUBLE), \
            'Vertex attribute must have signed type larger than byte'
        super(VertexAttribute, self).__init__(count, gl_type)

    def enable(self):
        glEnableClientState(GL_VERTEX_ARRAY)

    def set_pointer(self, pointer):
        glVertexPointer(self.count, self.gl_type, self.stride,
                        self.offset + pointer)

class GenericAttribute(AbstractAttribute):
    '''Generic vertex attribute, used by shader programs.'''

    def __init__(self, index, normalized, count, gl_type):
        self.normalized = bool(normalized)
        self.index = index
        super(GenericAttribute, self).__init__(count, gl_type)

    def enable(self):
        glEnableVertexAttribArray(self.index)

    def set_pointer(self, pointer):
        glVertexAttribPointer(self.index, self.count, self.gl_type,
                              self.normalized, self.stride, 
                              self.offset + pointer)

_attribute_classes = {
    'c': ColorAttribute,
    't': TexCoordAttribute,
    'v': VertexAttribute,
}


###############################################################################
##                              vertexbuffer.py                              ##
###############################################################################

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

_enable_vbo = pyglet.options['graphics_vbo']

# Enable workaround permanently if any VBO is created on a context that has
# this workaround.  (On systems with multiple contexts where one is
# unaffected, the workaround will be enabled unconditionally on all of the
# contexts anyway.  This is completely unlikely anyway).
_workaround_vbo_finish = False

def create_buffer(size,
                  target=GL_ARRAY_BUFFER,
                  usage=GL_DYNAMIC_DRAW,
                  vbo=True):
    '''Create a buffer of vertex data.

    :Parameters:
        `size` : int
            Size of the buffer, in bytes
        `target` : int
            OpenGL target buffer
        `usage` : int
            OpenGL usage constant
        `vbo` : bool
            True if a `VertexBufferObject` should be created if the driver
            supports it; otherwise only a `VertexArray` is created.

    :rtype: `AbstractBuffer`
    '''
    from pyglet import gl
    if (vbo and
        gl_info.have_version(1, 5) and
        _enable_vbo and
        not gl.current_context._workaround_vbo):
        return VertexBufferObject(size, target, usage)
    else:
        return VertexArray(size)

def create_mappable_buffer(size,
                           target=GL_ARRAY_BUFFER,
                           usage=GL_DYNAMIC_DRAW,
                           vbo=True):
    '''Create a mappable buffer of vertex data.

    :Parameters:
        `size` : int
            Size of the buffer, in bytes
        `target` : int
            OpenGL target buffer
        `usage` : int
            OpenGL usage constant
        `vbo` : bool
            True if a `VertexBufferObject` should be created if the driver
            supports it; otherwise only a `VertexArray` is created.

    :rtype: `AbstractBuffer` with `AbstractMappable`
    '''
    from pyglet import gl
    if (vbo and
        gl_info.have_version(1, 5) and
        _enable_vbo and
        not gl.current_context._workaround_vbo):
        return MappableVertexBufferObject(size, target, usage)
    else:
        return VertexArray(size)

class AbstractBuffer(object):
    '''Abstract buffer of byte data.

    :Ivariables:
        `size` : int
            Size of buffer, in bytes
        `ptr` : int
            Memory offset of the buffer, as used by the ``glVertexPointer``
            family of functions
        `target` : int
            OpenGL buffer target, for example ``GL_ARRAY_BUFFER``
        `usage` : int
            OpenGL buffer usage, for example ``GL_DYNAMIC_DRAW``

    '''

    ptr = 0
    size = 0

    def bind(self):
        '''Bind this buffer to its OpenGL target.'''
        raise NotImplementedError('abstract')

    def unbind(self):
        '''Reset the buffer's OpenGL target.'''
        raise NotImplementedError('abstract')

    def set_data(self, data):
        '''Set the entire contents of the buffer.

        :Parameters:
            `data` : sequence of int or ctypes pointer
                The byte array to set.

        '''
        raise NotImplementedError('abstract')

    def set_data_region(self, data, start, length):
        '''Set part of the buffer contents.

        :Parameters:
            `data` : sequence of int or ctypes pointer
                The byte array of data to set
            `start` : int
                Offset to start replacing data
            `length` : int
                Length of region to replace

        '''
        raise NotImplementedError('abstract')

    def map(self, invalidate=False):
        '''Map the entire buffer into system memory.

        The mapped region must be subsequently unmapped with `unmap` before
        performing any other operations on the buffer.

        :Parameters:
            `invalidate` : bool
                If True, the initial contents of the mapped block need not
                reflect the actual contents of the buffer.

        :rtype: ``POINTER(ctypes.c_ubyte)``
        :return: Pointer to the mapped block in memory
        '''
        raise NotImplementedError('abstract')

    def unmap(self):
        '''Unmap a previously mapped memory block.'''
        raise NotImplementedError('abstract')

    def resize(self, size):
        '''Resize the buffer to a new size.

        :Parameters:
            `size` : int
                New size of the buffer, in bytes

        '''

    def delete(self):
        '''Delete this buffer, reducing system resource usage.'''
        raise NotImplementedError('abstract')

class AbstractMappable(object):
    def get_region(self, start, size, ptr_type):
        '''Map a region of the buffer into a ctypes array of the desired
        type.  This region does not need to be unmapped, but will become
        invalid if the buffer is resized.

        Note that although a pointer type is required, an array is mapped.
        For example::

            get_region(0, ctypes.sizeof(c_int) * 20, ctypes.POINTER(c_int * 20))

        will map bytes 0 to 80 of the buffer to an array of 20 ints.

        Changes to the array may not be recognised until the region's
        `AbstractBufferRegion.invalidate` method is called.

        :Parameters:
            `start` : int
                Offset into the buffer to map from, in bytes
            `size` : int
                Size of the buffer region to map, in bytes
            `ptr_type` : ctypes pointer type
                Pointer type describing the array format to create

        :rtype: `AbstractBufferRegion`
        '''
        raise NotImplementedError('abstract')

class VertexArray(AbstractBuffer, AbstractMappable):
    '''A ctypes implementation of a vertex array.

    Many of the methods on this class are effectively no-op's, such as `bind`,
    `unbind`, `map`, `unmap` and `delete`; they exist in order to present
    a consistent interface with `VertexBufferObject`.

    This buffer type is also mappable, and so `get_region` can be used.
    '''

    def __init__(self, size):
        self.size = size

        self.array = (ctypes.c_byte * size)()
        self.ptr = ctypes.cast(self.array, ctypes.c_void_p).value

    def bind(self):
        pass

    def unbind(self):
        pass

    def set_data(self, data):
        ctypes.memmove(self.ptr, data, self.size)

    def set_data_region(self, data, start, length):
        ctypes.memmove(self.ptr + start, data, length)

    def map(self, invalidate=False):
        return self.array

    def unmap(self):
        pass

    def get_region(self, start, size, ptr_type):
        array = ctypes.cast(self.ptr + start, ptr_type).contents
        return VertexArrayRegion(array)

    def delete(self):
        pass

    def resize(self, size):
        array = (ctypes.c_byte * size)()
        ctypes.memmove(array, self.array, min(size, self.size))
        self.size = size
        self.array = array
        self.ptr = ctypes.cast(self.array, ctypes.c_void_p).value


class VertexBufferObject(AbstractBuffer):
    '''Lightweight representation of an OpenGL VBO.

    The data in the buffer is not replicated in any system memory (unless it
    is done so by the video driver).  While this can improve memory usage and
    possibly performance, updates to the buffer are relatively slow.

    This class does not implement `AbstractMappable`, and so has no
    ``get_region`` method.  See `MappableVertexBufferObject` for a VBO class
    that does implement ``get_region``.
    '''

    def __init__(self, size, target, usage):
        self.size = size
        self.target = target
        self.usage = usage
        self._context = pyglet.gl.current_context

        id = GLuint()
        glGenBuffers(1, id)
        self.id = id.value
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glBindBuffer(target, self.id)
        glBufferData(target, self.size, None, self.usage)
        glPopClientAttrib()

        global _workaround_vbo_finish
        if pyglet.gl.current_context._workaround_vbo_finish:
            _workaround_vbo_finish = True

    def bind(self):
        glBindBuffer(self.target, self.id)

    def unbind(self):
        glBindBuffer(self.target, 0)

    def set_data(self, data):
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glBindBuffer(self.target, self.id)
        glBufferData(self.target, self.size, data, self.usage)
        glPopClientAttrib()

    def set_data_region(self, data, start, length):
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glBindBuffer(self.target, self.id)
        glBufferSubData(self.target, start, length, data)
        glPopClientAttrib()

    def map(self, invalidate=False):
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glBindBuffer(self.target, self.id)
        if invalidate:
            glBufferData(self.target, self.size, None, self.usage)
        ptr = ctypes.cast(glMapBuffer(self.target, GL_WRITE_ONLY),
                          ctypes.POINTER(ctypes.c_byte * self.size)).contents
        glPopClientAttrib()
        return ptr

    def unmap(self):
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glUnmapBuffer(self.target)
        glPopClientAttrib()

    def __del__(self):
        try:
            if self.id is not None:
                self._context.delete_buffer(self.id)
        except:
            pass

    def delete(self):
        id = GLuint(self.id)
        glDeleteBuffers(1, id)
        self.id = None

    def resize(self, size):
        # Map, create a copy, then reinitialize.
        temp = (ctypes.c_byte * size)()

        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glBindBuffer(self.target, self.id)
        data = glMapBuffer(self.target, GL_READ_ONLY)
        ctypes.memmove(temp, data, min(size, self.size))
        glUnmapBuffer(self.target)

        self.size = size
        glBufferData(self.target, self.size, temp, self.usage)
        glPopClientAttrib()

class AbstractBufferRegion(object):
    '''A mapped region of a buffer.

    Buffer regions are obtained using `AbstractMappable.get_region`.

    :Ivariables:
        `array` : ctypes array
            Array of data, of the type and count requested by ``get_region``.

    '''
    def invalidate(self):
        '''Mark this region as changed.

        The buffer may not be updated with the latest contents of the
        array until this method is called.  (However, it may not be updated
        until the next time the buffer is used, for efficiency).
        '''
        pass

class VertexBufferObjectRegion(AbstractBufferRegion):
    '''A mapped region of a VBO.'''
    def __init__(self, buffer, start, end, array):
        self.buffer = buffer
        self.start = start
        self.end = end
        self.array = array

    def invalidate(self):
        buffer = self.buffer
        buffer._dirty_min = min(buffer._dirty_min, self.start)
        buffer._dirty_max = max(buffer._dirty_max, self.end)

class VertexArrayRegion(AbstractBufferRegion):
    '''A mapped region of a vertex array.

    The `invalidate` method is a no-op but is provided in order to present
    a consistent interface with `VertexBufferObjectRegion`.
    '''
    def __init__(self, array):
        self.array = array

###############################################################################
##                              vertexdomain.py                              ##
###############################################################################


__docformat__ = 'restructuredtext'
__version__ = '$Id: $'


_usage_format_re = re.compile(r'''
    (?P<attribute>[^/]*)
    (/ (?P<usage> static|dynamic|stream|none))?
''', re.VERBOSE)

_gl_usages = {
    'static': GL_STATIC_DRAW,
    'dynamic': GL_DYNAMIC_DRAW,
    'stream': GL_STREAM_DRAW,
    'none': GL_STREAM_DRAW_ARB, # Force no VBO
}

def _nearest_pow2(v):
    # From http://graphics.stanford.edu/~seander/bithacks.html#RoundUpPowerOf2
    # Credit: Sean Anderson
    v -= 1
    v |= v >> 1
    v |= v >> 2
    v |= v >> 4
    v |= v >> 8
    v |= v >> 16
    return v + 1

def create_attribute_usage(format):
    '''Create an attribute and usage pair from a format string.  The
    format string is as documented in `pyglet.graphics.vertexattribute`, with
    the addition of an optional usage component::

        usage ::= attribute ( '/' ('static' | 'dynamic' | 'stream' | 'none') )?

    If the usage is not given it defaults to 'dynamic'.  The usage corresponds
    to the OpenGL VBO usage hint, and for ``static`` also indicates a
    preference for interleaved arrays.  If ``none`` is specified a buffer
    object is not created, and vertex data is stored in system memory.
    
    Some examples:

    ``v3f/stream``
        3D vertex position using floats, for stream usage
    ``c4b/static``
        4-byte color attribute, for static usage

    :return: attribute, usage  
    '''
    match = _usage_format_re.match(format)
    attribute_format = match.group('attribute')
    attribute = create_attribute(attribute_format)
    usage = match.group('usage')
    if usage:
        vbo = not usage == 'none'
        usage = _gl_usages[usage]
    else:
        usage = GL_DYNAMIC_DRAW
        vbo = True

    return (attribute, usage, vbo)

def create_domain(*attribute_usage_formats):
    '''Create a vertex domain covering the given attribute usage formats.
    See documentation for `create_attribute_usage` and 
    `pyglet.graphics.vertexattribute.create_attribute` for the grammar of
    these format strings.

    :rtype: `VertexDomain`
    '''
    attribute_usages = [create_attribute_usage(f) \
                        for f in attribute_usage_formats]
    return VertexDomain(attribute_usages)

class VertexDomain(object):
    '''Management of a set of vertex lists.

    Construction of a vertex domain is usually done with the `create_domain`
    function.
    '''
    _version = 0
    _initial_count = 16

    def __init__(self, attribute_usages):
        self.allocator = Allocator(self._initial_count)

        static_attributes = []
        attributes = []
        self.buffer_attributes = []   # list of (buffer, attributes)
        for attribute, usage, vbo in attribute_usages:
            # Create non-interleaved buffer
            attributes.append(attribute)
            attribute.buffer = create_mappable_buffer(
                attribute.stride * self.allocator.capacity, 
                usage=usage, vbo=vbo)
            attribute.buffer.element_size = attribute.stride
            #attribute.buffer.attributes = (attribute,)
            self.buffer_attributes.append(
                (attribute.buffer, attribute))
        
        # Create named attributes for each attribute
        self.attributes = attributes
        self.attribute_names = {}
        for attribute in attributes:
            if isinstance(attribute, GenericAttribute):
                index = attribute.index
                if 'generic' not in self.attributes:
                    self.attribute_names['generic'] = {}
                assert index not in self.attribute_names['generic'], \
                    'More than one generic attribute with index %d' % index
                self.attribute_names['generic'][index] = attribute
            else:
                name = attribute.plural
                assert name not in self.attributes, \
                    'More than one "%s" attribute given' % name
                self.attribute_names[name] = attribute

    def __del__(self):
        # Break circular refs that Python GC seems to miss even when forced
        # collection.
        for attribute in self.attributes:
            del attribute.buffer

    def _safe_alloc(self, count):
        '''Allocate vertices, resizing the buffers if necessary.'''
        try:
            return self.allocator.alloc(count)
        except AllocatorMemoryException, e:
            capacity = _nearest_pow2(e.requested_capacity)
            self._version += 1
            for buffer, _ in self.buffer_attributes:
                buffer.resize(capacity * buffer.element_size)
            self.allocator.set_capacity(capacity)
            return self.allocator.alloc(count)

    def _safe_realloc(self, start, count, new_count):
        '''Reallocate vertices, resizing the buffers if necessary.'''
        try:
            return self.allocator.realloc(start, count, new_count)
        except AllocatorMemoryException, e:
            capacity = _nearest_pow2(e.requested_capacity)
            self._version += 1
            for buffer, _ in self.buffer_attributes:
                buffer.resize(capacity * buffer.element_size)
            self.allocator.set_capacity(capacity)
            return self.allocator.realloc(start, count, new_count) 

    def create(self, count):
        '''Create a `VertexList` in this domain.

        :Parameters:
            `count` : int
                Number of vertices to create.

        :rtype: `VertexList`
        '''
        start = self._safe_alloc(count)
        return VertexList(self, start, count)

    def draw(self, mode):
        '''Draw vertices in the domain.
        
        If `vertex_list` is not specified, all vertices in the domain are
        drawn.  This is the most efficient way to render primitives.

        If `vertex_list` specifies a `VertexList`, only primitives in that
        list will be drawn.

        :Parameters:
            `mode` : int
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
            `vertex_list` : `VertexList`
                Vertex list to draw, or ``None`` for all lists in this domain.

        '''
        
        starts, sizes = self.allocator.get_allocated_regions()
        primcount = len(starts)
        
        if primcount == 0:
            pass
        elif primcount == 1:
            glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
            for buffer, attribute in self.buffer_attributes:
                attribute.enable()
                attribute.set_pointer(attribute.buffer.ptr)
            if _workaround_vbo_finish:
                glFinish()

            # Common case
            glDrawArrays(mode, starts[0], sizes[0])
            glPopClientAttrib()

    def _is_empty(self):
        return not self.allocator.starts

    def __repr__(self):
        return '<%s@%x %s>' % (self.__class__.__name__, id(self), 
                               self.allocator)

class VertexList(object):
    '''A list of vertices within a `VertexDomain`.  Use
    `VertexDomain.create` to construct this list.
    '''
    
    def __init__(self, domain, start, count):
        # TODO make private
        self.domain = domain
        self.start = start
        self.count = count
    
    def get_size(self):
        '''Get the number of vertices in the list.

        :rtype: int
        '''
        return self.count

    def get_domain(self):
        '''Get the domain this vertex list belongs to.

        :rtype: `VertexDomain`
        '''
        return self.domain

    def draw(self, mode):
        '''Draw this vertex list in the given OpenGL mode.

        :Parameters:
            `mode` : int
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.

        '''
        self.domain.draw(mode, self)
    
    def resize(self, count):
        '''Resize this group.
        
        :Parameters:
            `count` : int
                New number of vertices in the list. 

        '''
        new_start = self.domain._safe_realloc(self.start, self.count, count)
        if new_start != self.start:
            # Copy contents to new location
            for attribute in self.domain.attributes:
                old = attribute.get_region(attribute.buffer, 
                                           self.start, self.count)
                new = attribute.get_region(attribute.buffer, 
                                           new_start, self.count)
                new.array[:] = old.array[:]
                new.invalidate()
        self.start = new_start
        self.count = count

        self._colors_cache_version = None
        self._fog_coords_cache_version = None
        self._edge_flags_cache_version = None
        self._normals_cache_version = None
        self._secondary_colors_cache_version = None
        self._tex_coords_cache_version = None
        self._vertices_cache_version = None

    def delete(self):
        '''Delete this group.'''
        self.domain.allocator.dealloc(self.start, self.count)

    def _set_attribute_data(self, i, data):
        attribute = self.domain.attributes[i]
        # TODO without region
        region = attribute.get_region(attribute.buffer, self.start, self.count)
        region.array[:] = data
        region.invalidate()

    # ---

    def _get_colors(self):
        if (self._colors_cache_version != self.domain._version):
            domain = self.domain
            attribute = domain.attribute_names['colors']
            self._colors_cache = attribute.get_region(
                attribute.buffer, self.start, self.count)
            self._colors_cache_version = domain._version

        region = self._colors_cache
        region.invalidate()
        return region.array

    def _set_colors(self, data):
        self._get_colors()[:] = data

    _colors_cache = None
    _colors_cache_version = None
    colors = property(_get_colors, _set_colors, 
                      doc='''Array of color data.''')

    # ---

    _tex_coords_cache = None
    _tex_coords_cache_version = None

    def _get_tex_coords(self):
        if (self._tex_coords_cache_version != self.domain._version):
            domain = self.domain
            attribute = domain.attribute_names['tex_coords']
            self._tex_coords_cache = attribute.get_region(
                attribute.buffer, self.start, self.count)
            self._tex_coords_cache_version = domain._version

        region = self._tex_coords_cache
        region.invalidate()
        return region.array

    def _set_tex_coords(self, data):
        self._get_tex_coords()[:] = data

    tex_coords = property(_get_tex_coords, _set_tex_coords,
                          doc='''Array of texture coordinate data.''')

    # ---
    
    _vertices_cache = None
    _vertices_cache_version = None

    def _get_vertices(self):
        if (self._vertices_cache_version != self.domain._version):
            domain = self.domain
            attribute = domain.attribute_names['vertices']
            self._vertices_cache = attribute.get_region(
                attribute.buffer, self.start, self.count)
            self._vertices_cache_version = domain._version

        region = self._vertices_cache
        region.invalidate()
        return region.array

    def _set_vertices(self, data):
        self._get_vertices()[:] = data
    
    vertices = property(_get_vertices, _set_vertices,
                        doc='''Array of vertex coordinate data.''')
