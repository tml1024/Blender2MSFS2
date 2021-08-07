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
import xml.etree.ElementTree as etree
from xml.dom import minidom #to make things pretty
from xml.dom.minidom import parse, parseString

import os.path
from os import urandom
import re
import itertools 

def generate_guid():
    b = bytearray(urandom(16))
    b[6] = (b[6]&0xf)|0x40 
    return "{"+str('%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x' % tuple(b))+"}"

def pretty_xml_given_root(root):
    """
    Useful for when you are editing xml data on the fly
    """
    xml_string = minidom.parseString(etree.tostring(root)).toprettyxml()
    xml_string = os.linesep.join([s for s in xml_string.splitlines() if s.strip()]) # remove the weird newline issue
    return xml_string

def save_xml(context, export_settings, lods=[]):
    """Creates/Appends the XML file for the MSFS model(s)"""

    xml_file = export_settings['gltf_filedirectory']+bpy.path.ensure_ext(export_settings['gltf_msfs_xml_file'],'.xml')

    root = None

    if os.path.exists(xml_file):
        with open(xml_file) as f:
            try:
                xml_string = f.read()
            except:
                msg= "Couldn't read the XML file under: <%s>"%xml_file
                print(msg)
                return 0
        
        #We need to remove the xml node to continue.
        xml_string = re.sub('<[?]xml.*[?]>', '', xml_string)

        #Since Asobo doesn't stick to conventions, we need to add a root-node to the file:
        xml_string = '<root>'+xml_string+'</root>'

        root = etree.fromstring(xml_string.lstrip())

        msfs_guid = ""

        #check the ModelInfo
        ModelInfo_node = root.find('ModelInfo')
        if ModelInfo_node == None:
            ModelInfo_node = etree.SubElement(root, "ModelInfo")
            ModelInfo_node.set('version', "1.1")
            if export_settings['gltf_msfs_generate_guid'] == True:
                msfs_guid = generate_guid()
                ModelInfo_node.set('guid',msfs_guid)
        else:
            if export_settings['gltf_msfs_generate_guid'] == True:
                if ('guid' in ModelInfo_node.attrib and 'guid' in ModelInfo_node.attrib != ""):
                    msfs_guid = ModelInfo_node.attrib['guid']
                else:
                    msfs_guid = generate_guid()

                ModelInfo_node.set('guid',msfs_guid)
        
        if len(lods) > 0:
            LODS_node = ModelInfo_node.find('LODS')
            if LODS_node == None:
                LODS_node = etree.SubElement(ModelInfo_node, "LODS")
            else:
                nodes_to_remove = []
                for lod in LODS_node:
                    #Delete all lod models:
                    if lod.tag == "LOD":
                        nodes_to_remove.append(lod)
                for node in reversed(nodes_to_remove):
                    LODS_node.remove(node)

            #re-generate the LODs:
            lod_size = []
            current_size = 0
            for model in reversed(lods):
                lod_size.insert(0,current_size)
                if current_size == 0:
                    current_size = 4
                else:
                    current_size = current_size * 2

            for (size, model) in zip(lod_size,lods):
                my_lod = etree.SubElement(LODS_node,"LOD")

                my_lod.set('ModelFile',os.path.basename(os.path.realpath(model)))
                if size != 0:
                    my_lod.set('minSize',str(size))

    else:
        root = etree.Element("root")
        ModelInfo_node = etree.SubElement(root, "ModelInfo")
        ModelInfo_node.set('version', "1.1")
        if export_settings['gltf_msfs_generate_guid'] == True:
            msfs_guid = generate_guid()
            ModelInfo_node.set('guid',msfs_guid)
        if len(lods) > 0:
            lod_size = []
            current_size = 0
            for model in reversed(lods):
                lod_size.insert(0,current_size)
                if current_size == 0:
                    current_size = 4
                else:
                    current_size = current_size * 2

            LODS_node = etree.SubElement(ModelInfo_node, "LODS")
            for (size, model) in zip(lod_size,lods):
                my_lod = etree.SubElement(LODS_node,"LOD")

                my_lod.set('ModelFile',os.path.basename(os.path.realpath(model)))
                if size != 0:
                    my_lod.set('minSize',str(size))

    # Create a string, make it pretty:
    xml_string = pretty_xml_given_root(root)

    # Remove root node:
    xml_string = re.sub('<root>', '', xml_string)
    xml_string = re.sub('</root>', '', xml_string)
    
    #Write to file:
    with open(xml_file, "w") as f:
        f.write(xml_string)









