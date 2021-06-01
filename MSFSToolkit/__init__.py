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

bl_info = {
    "name" : "MSFSToolkit",
    "author" : "Otmar Nitsche",
    "description" : "This toolkit prepares your 3D assets to be used for Microsoft Flight Simulator. Copyright (c) 2020 Otmar Nitsche",
    "blender" : (2, 82, 3),
    "version" : (0, 32, 1),
    "location" : "View3D",
    "warning" : "This version of the addon is work-in-progress. Don't use it in your active development cycle, as it adds variables and objects to the scene that may cause issues further down the line.",
    "category" : "3D View",
    "wiki_url": "https://www.fsdeveloper.com/wiki/index.php?title=Blender2MSFS"
}


from . import auto_load

from . func_behavior import *
from . func_xml import *
from . func_properties import *

from . li_material import *
from . li_properties import *

from . ui_materials import *
#from . ui_properties import *

##################################################################################
# Load custom glTF exporter and activate Asobo extensions:
from . exporter import *
from . extensions import *
##################################################################################

auto_load.init()

def register():
    auto_load.register()
    from .extensions import register
    register()
    from .exporter import register
    register()

    bpy.types.Scene.msfs_guid = bpy.props.StringProperty(name="GUID",default="")

def register_panel():
    from .extensions import register_panel
    register_panel()

def unregister():
    #from .extensions import unregister
    #unregister()
    #from .exporter import unregister
    #unregister()
    auto_load.unregister()

def unregister_panel():
    from .extensions import unregister_panel
    unregister_panel()
