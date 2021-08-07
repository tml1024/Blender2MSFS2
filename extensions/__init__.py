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

from . ext_master import *

def register():
    try:
        bpy.utils.register_class(ExtAsoboProperties)
    except Exception:
        pass
    bpy.types.Scene.msfs_extAsoboProperties = bpy.props.PointerProperty(type=ExtAsoboProperties)

def register_panel():
    # Register the panel on demand, we need to be sure to only register it once
    # This is necessary because the panel is a child of the extensions panel,
    # which may not be registered when we try to register this extension
    try:
        bpy.utils.register_class(GLTF_PT_AsoboExtensionPanel)
    except Exception:
        pass

    # If the glTF exporter is disabled, we need to unregister the extension panel
    # Just return a function to the exporter so it can unregister the panel
    return unregister_panel


def unregister_panel():
    # Since panel is registered on demand, it is possible it is not registered
    try:
        bpy.utils.unregister_class(GLTF_PT_AsoboExtensionPanel)
    except Exception:
        pass


def unregister():
    unregister_panel()
    try:
        bpy.utils.unregister_class(ExtAsoboProperties)
    except Exception:
        pass
    del bpy.types.Scene.msfs_extAsoboProperties