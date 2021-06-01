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

#from io_scene_gltf2 import *

bl_info = {
    'name': 'glTF 2.0 extended format',
    'author': 'Julien Duroure, Scurest, Norbert Nopper, Urs Hanselmann, Moritz Becher, Benjamin Schmithüsen, Jim Eckerlein, and many external contributors. Modified by Otmar Nitsche for use with the Blender2MSFS addon.',
    "version": (1, 0, 0),
    'blender': (2, 80, 0),
    'location': 'File > Export',
    'description': 'Export as extended glTF 2.0 for MSFS',
    'warning': '',
    'doc_url': "{BLENDER_MANUAL_URL}/addons/import_export/scene_gltf2.html",
    'tracker_url': "https://github.com/KhronosGroup/glTF-Blender-IO/issues/",
    'support': 'COMMUNITY',
    'category': 'Export',
}

def get_version_string():
    return str(bl_info['version'][0]) + '.' + str(bl_info['version'][1]) + '.' + str(bl_info['version'][2])

#
# Script reloading (if the user calls 'Reload Scripts' from Blender)
#

def reload_package(module_dict_main):
    import importlib
    from pathlib import Path

    def reload_package_recursive(current_dir, module_dict):
        for path in current_dir.iterdir():
            if "__init__" in str(path) or path.stem not in module_dict:
                continue

            if path.is_file() and path.suffix == ".py":
                importlib.reload(module_dict[path.stem])
            elif path.is_dir():
                reload_package_recursive(path, module_dict[path.stem].__dict__)

    reload_package_recursive(Path(__file__).parent, module_dict_main)


if "bpy" in locals():
    reload_package(locals())

import bpy
from bpy.props import (StringProperty,
                       BoolProperty,
                       EnumProperty,
                       IntProperty,
                       CollectionProperty)
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper, ExportHelper


#
#  Functions / Classes.
#

extension_panel_unregister_functors = []

class ExportExtendedGLTF2_Base:
    # TODO: refactor to avoid boilerplate

    def __init__(self):
        from io_scene_gltf2.io.exp import gltf2_io_draco_compression_extension
        self.is_draco_available = gltf2_io_draco_compression_extension.dll_exists()

    bl_options = {'PRESET'}

    export_format: EnumProperty(
        name='Format',
        items=(('GLB', 'glTF Binary (.glb)',
                'Exports a single file, with all data packed in binary form. '
                'Most efficient and portable, but more difficult to edit later'),
               ('GLTF_EMBEDDED', 'glTF Embedded (.gltf)',
                'Exports a single file, with all data packed in JSON. '
                'Less efficient than binary, but easier to edit later'),
               ('GLTF_SEPARATE', 'glTF Separate (.gltf + .bin + textures)',
                'Exports multiple files, with separate JSON, binary and texture data. '
                'Easiest to edit later')),
        description=(
            'Output format and embedding options. Binary is most efficient, '
            'but JSON (embedded or separate) may be easier to edit later'
        ),
        default='GLTF_SEPARATE'
    )

    ui_tab: EnumProperty(
        items=(('GENERAL', "General", "General settings"),
               ('MESHES', "Meshes", "Mesh settings"),
               ('OBJECTS', "Objects", "Object settings"),
               ('ANIMATION', "Animation", "Animation settings")),
        name="ui_tab",
        description="Export setting categories",
    )

    export_copyright: StringProperty(
        name='Copyright',
        description='Legal rights and conditions for the model',
        default=''
    )

    export_image_format: EnumProperty(
        name='Images',
        items=(('AUTO', 'Automatic',
                'Save PNGs as PNGs and JPEGs as JPEGs.\n'
                'If neither one, use PNG'),
                ('JPEG', 'JPEG Format (.jpg)',
                'Save images as JPEGs. (Images that need alpha are saved as PNGs though.)\n'
                'Be aware of a possible loss in quality'),
               ),
        description=(
            'Output format for images. PNG is lossless and generally preferred, but JPEG might be preferable for web '
            'applications due to the smaller file size'
        ),
        default='AUTO'
    )

    export_texture_dir: StringProperty(
        name='Textures',
        description='Folder to place texture files in. Relative to the .gltf file',
        default='',
    )

    #############################################
    #Special functionalities for batch export:
    export_lods: BoolProperty(
        name='Batch export Lods',
        description='Select this option to automatically split the scene into different models for LOD function in MSFS.',
        default=False
    )

    export_xml: BoolProperty(
        name='Generate/Append XML file',
        description='Automatically generate an XML file for the model',
        default=False
    )

    export_xml_file: StringProperty(
        name='XML Filename',
        description='filename of the XML file (will be generated in the folder of the glTF model files)',
        subtype='FILE_NAME',
        default=''
    )

    export_generate_guid: BoolProperty(
        name='Generate GUID',
        description='Auto-generate a GUID which will be set in the XML file.',
        default=False
    )
    #############################################

    export_texcoords: BoolProperty(
        name='UVs',
        description='Export UVs (texture coordinates) with meshes',
        default=True
    )

    export_normals: BoolProperty(
        name='Normals',
        description='Export vertex normals with meshes',
        default=True
    )

    export_draco_mesh_compression_enable: BoolProperty(
        name='Draco mesh compression',
        description='Compress mesh using Draco',
        default=False
    )

    export_draco_mesh_compression_level: IntProperty(
        name='Compression level',
        description='Compression level (0 = most speed, 6 = most compression, higher values currently not supported)',
        default=6,
        min=0,
        max=6
    )

    export_draco_position_quantization: IntProperty(
        name='Position quantization bits',
        description='Quantization bits for position values (0 = no quantization)',
        default=14,
        min=0,
        max=30
    )

    export_draco_normal_quantization: IntProperty(
        name='Normal quantization bits',
        description='Quantization bits for normal values (0 = no quantization)',
        default=10,
        min=0,
        max=30
    )

    export_draco_texcoord_quantization: IntProperty(
        name='Texcoord quantization bits',
        description='Quantization bits for texture coordinate values (0 = no quantization)',
        default=12,
        min=0,
        max=30
    )

    export_draco_generic_quantization: IntProperty(
        name='Generic quantization bits',
        description='Quantization bits for generic coordinate values like weights or joints (0 = no quantization)',
        default=12,
        min=0,
        max=30
    )

    export_tangents: BoolProperty(
        name='Tangents',
        description='Export vertex tangents with meshes',
        default=False
    )

    export_materials: BoolProperty(
        name='Materials',
        description='Export materials',
        default=True
    )

    export_colors: BoolProperty(
        name='Vertex Colors',
        description='Export vertex colors with meshes',
        default=True
    )

    export_cameras: BoolProperty(
        name='Cameras',
        description='Export cameras',
        default=False
    )

    # keep it for compatibility (for now)
    export_selected: BoolProperty(
        name='Selected Objects',
        description='Export selected objects only',
        default=False
    )

    use_selection: BoolProperty(
        name='Selected Objects',
        description='Export selected objects only',
        default=False
    )

    export_extras: BoolProperty(
        name='Custom Properties',
        description='Export custom properties as glTF extras',
        default=False
    )

    export_yup: BoolProperty(
        name='+Y Up',
        description='Export using glTF convention, +Y up',
        default=True
    )

    export_apply: BoolProperty(
        name='Apply Modifiers',
        description='Apply modifiers (excluding Armatures) to mesh objects -'
                    'WARNING: prevents exporting shape keys',
        default=False
    )

    export_animations: BoolProperty(
        name='Animations',
        description='Exports active actions and NLA tracks as glTF animations',
        default=True
    )

    export_frame_range: BoolProperty(
        name='Limit to Playback Range',
        description='Clips animations to selected playback range',
        default=True
    )

    export_frame_step: IntProperty(
        name='Sampling Rate',
        description='How often to evaluate animated values (in frames)',
        default=1,
        min=1,
        max=120
    )

    export_force_sampling: BoolProperty(
        name='Always Sample Animations',
        description='Apply sampling to all animations',
        default=True
    )

    export_nla_strips: BoolProperty(
        name='Group by NLA Track',
        description=(
            "When on, multiple actions become part of the same glTF animation if\n"
            "they're pushed onto NLA tracks with the same name.\n"
            "When off, all the currently assigned actions become one glTF animation"
        ),
        default=True
    )

    export_def_bones: BoolProperty(
        name='Export Deformation Bones Only',
        description='Export Deformation bones only (and needed bones for hierarchy)',
        default=False
    )

    export_current_frame: BoolProperty(
        name='Use Current Frame',
        description='Export the scene in the current animation frame',
        default=False
    )

    export_skins: BoolProperty(
        name='Skinning',
        description='Export skinning (armature) data',
        default=True
    )

    export_all_influences: BoolProperty(
        name='Include All Bone Influences',
        description='Allow >4 joint vertex influences. Models may appear incorrectly in many viewers',
        default=False
    )

    export_morph: BoolProperty(
        name='Shape Keys',
        description='Export shape keys (morph targets)',
        default=True
    )

    export_morph_normal: BoolProperty(
        name='Shape Key Normals',
        description='Export vertex normals with shape keys (morph targets)',
        default=True
    )

    export_morph_tangent: BoolProperty(
        name='Shape Key Tangents',
        description='Export vertex tangents with shape keys (morph targets)',
        default=False
    )

    export_lights: BoolProperty(
        name='Punctual Lights',
        description='Export directional, point, and spot lights. '
                    'Uses "KHR_lights_punctual" glTF extension',
        default=False
    )

    export_displacement: BoolProperty(
        name='Displacement Textures (EXPERIMENTAL)',
        description='EXPERIMENTAL: Export displacement textures. '
                    'Uses incomplete "KHR_materials_displacement" glTF extension',
        default=False
    )

    will_save_settings: BoolProperty(
        name='Remember Export Settings',
        description='Store glTF export settings in the Blender project',
        default=False)

    # Custom scene property for saving settings
    scene_key = "glTF2ExportSettings"

    def invoke(self, context, event):
        settings = context.scene.get(self.scene_key)
        self.will_save_settings = False
        if settings:
            try:
                for (k, v) in settings.items():
                    if k == "export_selected": # Back compatibility for export_selected --> use_selection
                        setattr(self, "use_selection", v)
                        del settings[k]
                        settings["use_selection"] = v
                        print("export_selected is now renamed use_selection, and will be deleted in a few release")
                    else:
                        setattr(self, k, v)
                self.will_save_settings = True

            except (AttributeError, TypeError):
                self.report({"ERROR"}, "Loading export settings failed. Removed corrupted settings")
                del context.scene[self.scene_key]

        import sys
        preferences = bpy.context.preferences
        for addon_name in preferences.addons.keys():
            try:
                if hasattr(sys.modules[addon_name], 'glTF2ExportUserExtension') or hasattr(sys.modules[addon_name], 'glTF2ExportUserExtensions'):
                    extension_panel_unregister_functors.append(sys.modules[addon_name].register_panel())
            except Exception:
                pass

        self.has_active_extenions = len(extension_panel_unregister_functors) > 0
        return ExportHelper.invoke(self, context, event)

    def save_settings(self, context):
        # find all export_ props
        all_props = self.properties
        export_props = {x: getattr(self, x) for x in dir(all_props)
                        if (x.startswith("export_") or x == "use_selection") and all_props.get(x) is not None}

        context.scene[self.scene_key] = export_props

    def execute(self, context):
        import os
        import datetime
        from .exp import gltf2_blender_export
        from .exp import gltf2_blender_batch_export

        if self.will_save_settings:
            self.save_settings(context)

        if self.export_format == 'GLB':
            self.filename_ext = '.glb'
        else:
            self.filename_ext = '.gltf'

        # All custom export settings are stored in this container.
        export_settings = {}

        export_settings['timestamp'] = datetime.datetime.now()

        export_settings['gltf_filepath'] = bpy.path.ensure_ext(self.filepath, self.filename_ext)
        export_settings['gltf_filedirectory'] = os.path.dirname(export_settings['gltf_filepath']) + '/'
        export_settings['gltf_texturedirectory'] = os.path.join(
            export_settings['gltf_filedirectory'],
            self.export_texture_dir,
        )

        #############################################
        # Special MSFS functionality:
        export_settings['gltf_msfs_lods'] = self.export_lods
        export_settings['gltf_msfs_xml'] = self.export_xml
        export_settings['gltf_msfs_xml_file'] = self.export_xml_file
        export_settings['gltf_msfs_generate_guid'] = self.export_xml and self.export_generate_guid
        #############################################

        export_settings['gltf_format'] = self.export_format
        export_settings['gltf_image_format'] = self.export_image_format
        export_settings['gltf_copyright'] = self.export_copyright
        export_settings['gltf_texcoords'] = self.export_texcoords
        export_settings['gltf_normals'] = self.export_normals
        export_settings['gltf_tangents'] = self.export_tangents and self.export_normals

        if self.is_draco_available:
            export_settings['gltf_draco_mesh_compression'] = self.export_draco_mesh_compression_enable
            export_settings['gltf_draco_mesh_compression_level'] = self.export_draco_mesh_compression_level
            export_settings['gltf_draco_position_quantization'] = self.export_draco_position_quantization
            export_settings['gltf_draco_normal_quantization'] = self.export_draco_normal_quantization
            export_settings['gltf_draco_texcoord_quantization'] = self.export_draco_texcoord_quantization
            export_settings['gltf_draco_generic_quantization'] = self.export_draco_generic_quantization
        else:
            export_settings['gltf_draco_mesh_compression'] = False

        export_settings['gltf_materials'] = self.export_materials
        export_settings['gltf_colors'] = self.export_colors
        export_settings['gltf_cameras'] = self.export_cameras

        # compatibility after renaming export_selected to use_selection
        if self.export_selected is True:
            self.report({"WARNING"}, "export_selected is now renamed use_selection, and will be deleted in a few release")
            export_settings['gltf_selected'] = self.export_selected
        else:
            export_settings['gltf_selected'] = self.use_selection

        # export_settings['gltf_selected'] = self.use_selection This can be uncomment when removing compatibility of export_selected
        export_settings['gltf_layers'] = True  # self.export_layers
        export_settings['gltf_extras'] = self.export_extras
        export_settings['gltf_yup'] = self.export_yup
        export_settings['gltf_apply'] = self.export_apply
        export_settings['gltf_current_frame'] = self.export_current_frame
        export_settings['gltf_animations'] = self.export_animations
        if self.export_animations:
            export_settings['gltf_frame_range'] = self.export_frame_range
            export_settings['gltf_force_sampling'] = self.export_force_sampling
            if self.export_force_sampling:
                export_settings['gltf_def_bones'] = self.export_def_bones
            else:
                export_settings['gltf_def_bones'] = False
            export_settings['gltf_nla_strips'] = self.export_nla_strips
        else:
            export_settings['gltf_frame_range'] = False
            export_settings['gltf_move_keyframes'] = False
            export_settings['gltf_force_sampling'] = False
            export_settings['gltf_def_bones'] = False
        export_settings['gltf_skins'] = self.export_skins
        if self.export_skins:
            export_settings['gltf_all_vertex_influences'] = self.export_all_influences
        else:
            export_settings['gltf_all_vertex_influences'] = False
        export_settings['gltf_frame_step'] = self.export_frame_step
        export_settings['gltf_morph'] = self.export_morph
        if self.export_morph:
            export_settings['gltf_morph_normal'] = self.export_morph_normal
        else:
            export_settings['gltf_morph_normal'] = False
        if self.export_morph and self.export_morph_normal:
            export_settings['gltf_morph_tangent'] = self.export_morph_tangent
        else:
            export_settings['gltf_morph_tangent'] = False

        export_settings['gltf_lights'] = self.export_lights
        export_settings['gltf_displacement'] = self.export_displacement

        export_settings['gltf_binary'] = bytearray()
        export_settings['gltf_binaryfilename'] = os.path.splitext(os.path.basename(
            bpy.path.ensure_ext(self.filepath,self.filename_ext)))[0] + '.bin'

        user_extensions = []
        pre_export_callbacks = []
        post_export_callbacks = []

        import sys
        preferences = bpy.context.preferences
        for addon_name in preferences.addons.keys():
            try:
                module = sys.modules[addon_name]
            except Exception:
                continue
            if hasattr(module, 'glTF2ExportUserExtension'):
                extension_ctor = module.glTF2ExportUserExtension
                user_extensions.append(extension_ctor())
            if hasattr(module, 'glTF2ExportUserExtensions'):
                extension_ctors = module.glTF2ExportUserExtensions
                for extension_ctor in extension_ctors:
                    user_extensions.append(extension_ctor())
            if hasattr(module, 'glTF2_pre_export_callback'):
                pre_export_callbacks.append(module.glTF2_pre_export_callback)
            if hasattr(module, 'glTF2_post_export_callback'):
                post_export_callbacks.append(module.glTF2_post_export_callback)
        export_settings['gltf_user_extensions'] = user_extensions
        export_settings['pre_export_callbacks'] = pre_export_callbacks
        export_settings['post_export_callbacks'] = post_export_callbacks

        if self.export_lods == True:
            return gltf2_blender_batch_export.save_ext_gltf(context, export_settings)
        else:
            return gltf2_blender_export.save_ext_gltf(context, export_settings)

    def draw(self, context):
        pass # Is needed to get panels available


class GLTF_PT_export_main_ext_gltf(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = ""
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_ext_gltf"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, 'export_format')
        if operator.export_format == 'GLTF_SEPARATE':
            layout.prop(operator, 'export_texture_dir', icon='FILE_FOLDER')
        layout.prop(operator, 'export_copyright')
        layout.prop(operator, 'will_save_settings')


class GLTF_PT_export_special_msfs(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "MSFS"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_ext_gltf"

    def draw(self, context):
        from bpy_extras.io_utils import ExportHelper

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        col = layout.column(align=True)#heading = "Limit to", align = True)
        #Special functions for MSFS export:
        layout.prop(operator, 'export_lods')
        layout.prop(operator, 'export_xml')
        if operator.export_xml == True:
            layout.prop(operator, 'export_xml_file', icon='FILE')
            layout.prop(operator, 'export_generate_guid')


class GLTF_PT_export_include_ext_gltf(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_ext_gltf"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        col = layout.column(align=True)#heading = "Limit to", align = True)
        col.prop(operator, 'use_selection')

        col = layout.column(align=True)#heading = "Data", align = True)
        col.prop(operator, 'export_extras')
        col.prop(operator, 'export_cameras')
        col.prop(operator, 'export_lights')


class GLTF_PT_export_transform_ext_gltf(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_ext_gltf"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, 'export_yup')


class GLTF_PT_export_geometry_ext_gltf(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_ext_gltf"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, 'export_apply')
        layout.prop(operator, 'export_texcoords')
        layout.prop(operator, 'export_normals')
        col = layout.column()
        col.active = operator.export_normals
        col.prop(operator, 'export_tangents')
        layout.prop(operator, 'export_colors')
        layout.prop(operator, 'export_materials')
        col = layout.column()
        col.active = operator.export_materials
        col.prop(operator, 'export_image_format')


class GLTF_PT_export_geometry_compression_ext_gltf(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Compression"
    bl_parent_id = "GLTF_PT_export_geometry"
    bl_options = {'DEFAULT_CLOSED'}

    def __init__(self):
        from io_scene_gltf2.io.exp import gltf2_io_draco_compression_extension
        self.is_draco_available = gltf2_io_draco_compression_extension.dll_exists(quiet=True)

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        if operator.is_draco_available:
            return operator.bl_idname == "EXPORT_SCENE_OT_ext_gltf"

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator
        self.layout.prop(operator, "export_draco_mesh_compression_enable", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.active = operator.export_draco_mesh_compression_enable
        layout.prop(operator, 'export_draco_mesh_compression_level')

        col = layout.column(align=True)
        col.prop(operator, 'export_draco_position_quantization', text="Quantize Position")
        col.prop(operator, 'export_draco_normal_quantization', text="Normal")
        col.prop(operator, 'export_draco_texcoord_quantization', text="Tex Coords")
        col.prop(operator, 'export_draco_generic_quantization', text="Generic")


class GLTF_PT_export_animation_ext_gltf(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Animation"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_ext_gltf"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, 'export_current_frame')


class GLTF_PT_export_animation_export_ext_gltf(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Animation"
    bl_parent_id = "GLTF_PT_export_animation"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_ext_gltf"

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator
        self.layout.prop(operator, "export_animations", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.active = operator.export_animations

        layout.prop(operator, 'export_frame_range')
        layout.prop(operator, 'export_frame_step')
        layout.prop(operator, 'export_force_sampling')
        layout.prop(operator, 'export_nla_strips')

        row = layout.row()
        row.active = operator.export_force_sampling
        row.prop(operator, 'export_def_bones')


class GLTF_PT_export_animation_shapekeys_ext_gltf(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Shape Keys"
    bl_parent_id = "GLTF_PT_export_animation"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_ext_gltf"

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator
        self.layout.prop(operator, "export_morph", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.active = operator.export_morph

        layout.prop(operator, 'export_morph_normal')
        col = layout.column()
        col.active = operator.export_morph_normal
        col.prop(operator, 'export_morph_tangent')


class GLTF_PT_export_animation_skinning_ext_gltf(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Skinning"
    bl_parent_id = "GLTF_PT_export_animation"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_ext_gltf"

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator
        self.layout.prop(operator, "export_skins", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.active = operator.export_skins
        layout.prop(operator, 'export_all_influences')


class GLTF_PT_export_user_extensions(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Extensions"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_ext_gltf" and operator.has_active_extenions

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.


class ExportExtendedGLTF2(bpy.types.Operator, ExportExtendedGLTF2_Base, ExportHelper):
    """Export scene as extended glTF 2.0 file for MSFS"""
    bl_idname = 'export_scene.ext_gltf'
    bl_label = 'Export extended glTF 2.0'

    filename_ext = ''

    filter_glob: StringProperty(default='*.glb;*.gltf', options={'HIDDEN'})


def menu_func_export(self, context):
    self.layout.operator(ExportExtendedGLTF2.bl_idname, text='extended glTF 2.0 (.glb/.gltf) for MSFS')


classes = (
    ExportExtendedGLTF2,
    GLTF_PT_export_main_ext_gltf,
    GLTF_PT_export_special_msfs,
    GLTF_PT_export_include_ext_gltf,
    GLTF_PT_export_transform_ext_gltf,
    GLTF_PT_export_geometry_ext_gltf,
    GLTF_PT_export_geometry_compression_ext_gltf,
    GLTF_PT_export_animation_ext_gltf,
    GLTF_PT_export_animation_export_ext_gltf,
    GLTF_PT_export_animation_shapekeys_ext_gltf,
    GLTF_PT_export_animation_skinning_ext_gltf,
    GLTF_PT_export_user_extensions,
)


def register():
    for c in classes:
        try:
            bpy.utils.register_class(c)
        except:
            pass
    # bpy.utils.register_module(__name__)

    # add to the export / import menu
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    for f in extension_panel_unregister_functors:
        f()
    extension_panel_unregister_functors.clear()

    # bpy.utils.unregister_module(__name__)

    # remove from the export / import menu
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
