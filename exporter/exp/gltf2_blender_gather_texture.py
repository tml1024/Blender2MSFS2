# Copyright 2018-2019 The glTF-Blender-IO authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import typing
import bpy
from .gltf2_blender_gather_cache import cached

from ..com import gltf2_io
from . import gltf2_blender_gather_sampler
from . import gltf2_blender_search_node_tree
from . import gltf2_blender_gather_image
from ..com import gltf2_io_debug
from .gltf2_io_user_extensions import export_user_extensions


@cached
def gather_texture(
        blender_shader_sockets_or_texture_slots: typing.Union[
            typing.Tuple[bpy.types.NodeSocket], typing.Tuple[typing.Any]],
        export_settings):
    """
    Gather texture sampling information and image channels from a blender shader texture attached to a shader socket.

    :param blender_shader_sockets: The sockets of the material which should contribute to the texture
    :param export_settings: configuration of the export
    :return: a glTF 2.0 texture with sampler and source embedded (will be converted to references by the exporter)
    """
    # TODO: extend to texture slots
    if not __filter_texture(blender_shader_sockets_or_texture_slots, export_settings):
        return None

    texture = gltf2_io.Texture(
        extensions=__gather_extensions(blender_shader_sockets_or_texture_slots, export_settings),
        extras=__gather_extras(blender_shader_sockets_or_texture_slots, export_settings),
        name=__gather_name(blender_shader_sockets_or_texture_slots, export_settings),
        sampler=__gather_sampler(blender_shader_sockets_or_texture_slots, export_settings),
        source=__gather_source(blender_shader_sockets_or_texture_slots, export_settings)
    )

    # although valid, most viewers can't handle missing source properties
    if texture.source is None:
        return None

    export_user_extensions('gather_texture_hook', export_settings, texture, blender_shader_sockets_or_texture_slots)

    return texture


def __filter_texture(blender_shader_sockets_or_texture_slots, export_settings):
    return True


def __gather_extensions(blender_shader_sockets, export_settings):
    return None


def __gather_extras(blender_shader_sockets, export_settings):
    return None


def __gather_name(blender_shader_sockets, export_settings):
    return None


def __gather_sampler(blender_shader_sockets_or_texture_slots, export_settings):
    if isinstance(blender_shader_sockets_or_texture_slots[0], bpy.types.NodeSocket):
        shader_nodes = [__get_tex_from_socket(socket).shader_node for socket in blender_shader_sockets_or_texture_slots]
        if len(shader_nodes) > 1:
            gltf2_io_debug.print_console("WARNING",
                                         "More than one shader node tex image used for a texture. "
                                         "The resulting glTF sampler will behave like the first shader node tex image.")
        return gltf2_blender_gather_sampler.gather_sampler(
            shader_nodes[0],
            export_settings)
    elif isinstance(blender_shader_sockets_or_texture_slots[0], bpy.types.MaterialTextureSlot):
        return gltf2_blender_gather_sampler.gather_sampler_from_texture_slot(
            blender_shader_sockets_or_texture_slots[0],
            export_settings
        )
    else:
        # TODO: implement texture slot sampler
        raise NotImplementedError()


def __gather_source(blender_shader_sockets_or_texture_slots, export_settings):
    return gltf2_blender_gather_image.gather_image(blender_shader_sockets_or_texture_slots, export_settings)

# Helpers


def __get_tex_from_socket(socket):
    result = gltf2_blender_search_node_tree.from_socket(
        socket,
        gltf2_blender_search_node_tree.FilterByType(bpy.types.ShaderNodeTexImage))
    if not result:
        return None
    return result[0]
