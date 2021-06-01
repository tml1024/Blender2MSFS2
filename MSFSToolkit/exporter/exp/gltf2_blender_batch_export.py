###################################################################################################
#
# Copyright 2020 Otmar Nitsche
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###################################################################################################
#
#   This is the modified exporter for the Blender2MSFS addon.
#   The only purpose of the modification is to allow for extensions
#   in the "asset" section of the glTF file.
#
###################################################################################################

import bpy
import time
import re
import os
from ..com.gltf2_io_debug import print_console, print_newline
from .gltf2_blender_gltf2_exporter import GlTF2Exporter
from . import gltf2_io_draco_compression_extension
from .gltf2_io_user_extensions import export_user_extensions

def save_ext_gltf(context, export_settings):
    """Go through the collections and find the lods, export them one by one."""
    
    from . import gltf2_blender_export

    lods = []
    pattern = re.compile("[Xx]\d+")
    rpattern = re.compile("[Xx]")
    filename_base, extension = os.path.splitext(export_settings['gltf_filepath'])
    filename, extension = os.path.splitext(os.path.basename(export_settings['gltf_filepath']))

    lod_model_export_settings = export_settings.copy()
    
    for collection in bpy.data.collections:
        if pattern.match(collection.name):
            #save collection name in export settings:
            lod_model_export_settings['gltf_current_collection'] = collection.name

            lod_id = str(rpattern.subn('_LOD', collection.name)[0])
            lod_filename = filename_base+lod_id+extension
            lods.append(lod_filename)

            lod_model_export_settings['gltf_filepath'] = lod_filename
            lod_model_export_settings['gltf_binaryfilename'] = filename+lod_id+'.bin'

            
            # Begin export process:
            original_frame = bpy.context.scene.frame_current
            if not lod_model_export_settings['gltf_current_frame']:
                bpy.context.scene.frame_set(0)

            gltf2_blender_export.__notify_start_ext_gltf(context)
            start_time = time.time()
            pre_export_callbacks = lod_model_export_settings["pre_export_callbacks"]
            for callback in pre_export_callbacks:
                callback(lod_model_export_settings)

            json, buffer = __export_ext_gltf(lod_model_export_settings)

            post_export_callbacks = lod_model_export_settings["post_export_callbacks"]
            for callback in post_export_callbacks:
                callback(lod_model_export_settings)
            gltf2_blender_export.__write_file_ext_gltf(json, buffer, lod_model_export_settings)

            end_time = time.time()
            gltf2_blender_export.__notify_end_ext_gltf(context, end_time - start_time)

            if not lod_model_export_settings['gltf_current_frame']:
                bpy.context.scene.frame_set(original_frame)
            
    #save XML file if required:
    if export_settings['gltf_msfs_xml'] == True:
        from .msfs_xml_export import save_xml
        save_xml(context,export_settings,lods)

    if len(lods) == 1:
        msg = "Exported one lod model."
        print(msg)
        for filename in lods:
            print("<%s>"%filename)
        return{'FINISHED'}
    elif len(lods) > 1:
        msg = "Exported %i lod models."%len(lods)
        print(msg)
        for filename in lods:
            print("<%s>"%filename)
        return{'FINISHED'}
    else:
        msg = "ERROR: Could not find LODs in the scene. Collection names should be: 'X00','X01', 'X02', and so on."
        print(msg)
        return{'CANCELLED'}


def __export_ext_gltf(export_settings):
    from . import gltf2_blender_export

    exporter = GlTF2Exporter(export_settings)
    __gather_ext_gltf(exporter, export_settings)
    buffer = gltf2_blender_export.__create_buffer_ext_gltf(exporter, export_settings)
    exporter.finalize_images()
    json = gltf2_blender_export.__fix_json_ext_gltf(exporter.glTF.to_dict())

    return json, buffer

def __gather_ext_gltf(exporter, export_settings):
    from . import gltf2_blender_batch_gather
    active_scene_idx, scenes, animations = gltf2_blender_batch_gather.gather_gltf2(export_settings)
    #active_scene_idx, scenes, animations = gltf2_blender_gather.gather_gltf2(export_settings)

    plan = {'active_scene_idx': active_scene_idx, 'scenes': scenes, 'animations': animations}
    export_user_extensions('gather_gltf_hook', export_settings, plan)
    active_scene_idx, scenes, animations = plan['active_scene_idx'], plan['scenes'], plan['animations']

    if export_settings['gltf_draco_mesh_compression']:
        gltf2_io_draco_compression_extension.compress_scene_primitives(scenes, export_settings)
        exporter.add_draco_extension()

    for idx, scene in enumerate(scenes):
        exporter.add_scene(scene, idx==active_scene_idx)
    for animation in animations:
        exporter.add_animation(animation)
