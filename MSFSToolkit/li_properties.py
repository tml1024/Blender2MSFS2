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

import bpy

from bpy.props import IntProperty, BoolProperty, StringProperty, FloatProperty, EnumProperty, FloatVectorProperty, PointerProperty

class MSFS_attached_behavior(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name = "behavior", default = "")
    source_file: bpy.props.StringProperty(name = "filepath", subtype='FILE_NAME', default = "")
    source_filename: bpy.props.StringProperty(name = "filename", subtype='FILE_NAME', default = "")
    kf_start: bpy.props.IntProperty(name = "kf_start", min=0,  default = 0)
    kf_end: bpy.props.IntProperty(name = "kf_end", min=0,  default = 1)

bpy.utils.register_class(MSFS_attached_behavior)

class MSFS_LI_object_properties():
    bpy.types.Object.msfs_behavior = bpy.props.CollectionProperty(type = MSFS_attached_behavior)
    bpy.types.Object.msfs_active_behavior = bpy.props.IntProperty(name="active_behavior",min=0,default=0)

