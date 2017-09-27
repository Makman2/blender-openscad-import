# -*- coding: utf-8 -*-
from subprocess import CalledProcessError, check_call
import os
from tempfile import TemporaryDirectory
import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, IntProperty, PointerProperty, CollectionProperty
from bpy.types import Operator, AddonPreferences
from bpy_extras.io_utils import ImportHelper


bl_info = {
    "name": "OpenSCAD importer",
    "description": "Imports OpenSCAD (.scad) files.",
    "author": "Maqq",
    "version": (1, 2),
    "blender": (2, 73, 0),
    "location": "File > Import",
    "warning": "", # used for warning icon and text in addons panel
    "category": "Import-Export"
}


def read_openscad(preferences, filepath, scale):
    """ Exports stl using OpenSCAD and imports it. """
    from io_mesh_stl import stl_utils
    from io_mesh_stl import blender_utils
    from mathutils import Matrix

    openscad_path = preferences.filepath

    # Export stl from OpenSCAD
    try:
        with TemporaryDirectory() as tempdir:
            tempfile_path = os.path.join(tempdir, 'tempexport.stl')
            command = [openscad_path, '-o', tempfile_path, filepath]
            print("Executing command:", ' '.join(command))
            check_call(command)
            tris, normals, pts = stl_utils.read_stl(tempfile_path)

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action='DESELECT')

        global_matrix = Matrix.Scale(scale, 4) # Create 4x4 scale matrix
        obj_name = os.path.basename(filepath).split('.')[0]
        blender_utils.create_and_link_mesh(obj_name, tris, normals, pts, global_matrix)

    except CalledProcessError:
        print('Running OpenSCAD failed.')

    return {'FINISHED'}


class OpenSCADImporterPreferences(AddonPreferences):
    """ Addon preferences. """
    bl_idname = __name__

    filepath = StringProperty(
            name="Path to OpenSCAD executable",
            subtype='FILE_PATH',
            )

    def draw(self, context):
        self.layout.prop(self, "filepath")


class OpenSCADImporter(Operator, ImportHelper):
    """ Import OpenSCAD files. """
    bl_idname = "import_mesh.scad"
    bl_label = "Import OpenSCAD"

    # ImportHelper mixin class uses this
    filename_ext = ".scad"

    filter_glob = StringProperty(
            default="*.scad",
            options={'HIDDEN'},
            )

    scale = FloatProperty(name='Scale', default=1.0)

    def __init__(self):
        super(OpenSCADImporter, self).__init__()

    def execute(self, context):
        preferences = context.user_preferences.addons[__name__].preferences
        return read_openscad(preferences, self.filepath, self.scale)


def menu_func_import(self, context):
    self.layout.operator(OpenSCADImporter.bl_idname, text="OpenSCAD (.scad)")

def register():
    bpy.utils.register_class(OpenSCADImporter)
    bpy.utils.register_class(OpenSCADImporterPreferences)
    bpy.types.INFO_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(OpenSCADImporter)
    bpy.utils.unregister_class(OpenSCADImporterPreferences)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
