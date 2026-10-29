# FlipStudio Bridge — a Blender add-on.
#
# "Send to FlipStudio" exports the selected objects (modifiers and geometry
# nodes applied, i.e. the EVALUATED mesh) as glTF binary into an exchange
# folder and launches FlipStudio on that file; FlipStudio imports it through
# its scene-importer registry on start-up. "Import from FlipStudio" opens an
# exchange file (glTF / OBJ / FBX) with Blender's own importers.
#
# This add-on is a separate GPL work (Blender add-ons must be GPL-compatible).
# FlipStudio itself links none of this; the two talk only through files.
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "FlipStudio Bridge",
    "author": "FlipStudio project",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "File > Export > Send to FlipStudio;  File > Import > Import from FlipStudio",
    "description": "Send the selected objects to FlipStudio (evaluated geometry over glTF) and bring FlipStudio exchange files back",
    "category": "Import-Export",
}

import os
import subprocess
import tempfile
import time

import bpy
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper


# ---------------------------------------------------------------------------
# Preferences: where FlipStudio lives and where the exchange files go.
# ---------------------------------------------------------------------------

def _default_exe():
    candidates = [
        r"D:\git\VulkanGameEngine2ClaudeTeam\build\bin\FlipStudio.exe",
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "FlipStudio", "FlipStudio.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return ""


def _default_exchange_dir():
    return os.path.join(tempfile.gettempdir(), "FlipStudioExchange")


class FLIPSTUDIO_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    flipstudio_exe: StringProperty(
        name="FlipStudio executable",
        subtype="FILE_PATH",
        default=_default_exe(),
    )
    exchange_dir: StringProperty(
        name="Exchange folder",
        description="Where exchange files are written (a temp folder by default)",
        subtype="DIR_PATH",
        default=_default_exchange_dir(),
    )
    launch_flipstudio: BoolProperty(
        name="Launch FlipStudio after export",
        default=True,
    )

    def draw(self, context):
        col = self.layout.column()
        col.prop(self, "flipstudio_exe")
        col.prop(self, "exchange_dir")
        col.prop(self, "launch_flipstudio")


def _prefs(context):
    return context.preferences.addons[__name__].preferences


# ---------------------------------------------------------------------------
# Send to FlipStudio
# ---------------------------------------------------------------------------

class FLIPSTUDIO_OT_send(bpy.types.Operator):
    """Export the selected objects as evaluated glTF and open them in FlipStudio"""
    bl_idname = "flipstudio.send"
    bl_label = "Send to FlipStudio"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return any(o.type == "MESH" for o in context.selected_objects)

    def execute(self, context):
        prefs = _prefs(context)
        exchange = bpy.path.abspath(prefs.exchange_dir) or _default_exchange_dir()
        os.makedirs(exchange, exist_ok=True)

        stem = bpy.path.clean_name(context.active_object.name if context.active_object else "scene")
        path = os.path.join(exchange, "%s_%d.glb" % (stem, int(time.time())))

        # Blender's glTF exporter: selection only, modifiers applied (the
        # evaluated mesh, geometry nodes included), Y up (glTF's frame, which
        # FlipStudio's world shares), no animation or lights for the bridge.
        result = bpy.ops.export_scene.gltf(
            filepath=path,
            export_format="GLB",
            use_selection=True,
            export_apply=True,
            export_yup=True,
            export_animations=False,
            export_lights=False,
            export_cameras=False,
            export_materials="NONE",
        )
        if "FINISHED" not in result:
            self.report({"ERROR"}, "glTF export did not finish")
            return {"CANCELLED"}

        if prefs.launch_flipstudio:
            exe = bpy.path.abspath(prefs.flipstudio_exe)
            if not exe or not os.path.isfile(exe):
                self.report({"WARNING"}, "Exported to %s — set the FlipStudio executable in the add-on preferences to launch it" % path)
                return {"FINISHED"}
            # FlipStudio opens a foreign scene file from its command line
            # (LDC-647) and imports it into the start-up document.
            subprocess.Popen([exe, path], cwd=os.path.dirname(exe))
            self.report({"INFO"}, "Sent %s to FlipStudio" % os.path.basename(path))
        else:
            self.report({"INFO"}, "Exported %s" % path)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Import from FlipStudio
# ---------------------------------------------------------------------------

class FLIPSTUDIO_OT_import(bpy.types.Operator, ImportHelper):
    """Open a FlipStudio exchange file (glTF / OBJ / FBX) with Blender's importers"""
    bl_idname = "flipstudio.import_exchange"
    bl_label = "Import from FlipStudio"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".glb"
    filter_glob: StringProperty(default="*.glb;*.gltf;*.obj;*.fbx", options={"HIDDEN"})

    def invoke(self, context, event):
        prefs = _prefs(context)
        exchange = bpy.path.abspath(prefs.exchange_dir)
        if exchange and os.path.isdir(exchange) and not self.filepath:
            self.filepath = os.path.join(exchange, "")
        return ImportHelper.invoke(self, context, event)

    def execute(self, context):
        ext = os.path.splitext(self.filepath)[1].lower()
        if ext in (".glb", ".gltf"):
            return bpy.ops.import_scene.gltf(filepath=self.filepath)
        if ext == ".obj":
            return bpy.ops.wm.obj_import(filepath=self.filepath)
        if ext == ".fbx":
            return bpy.ops.import_scene.fbx(filepath=self.filepath)
        self.report({"ERROR"}, "Not an exchange format: %s" % ext)
        return {"CANCELLED"}


# ---------------------------------------------------------------------------
# Menus + registration
# ---------------------------------------------------------------------------

def _menu_export(self, context):
    self.layout.operator(FLIPSTUDIO_OT_send.bl_idname, icon="EXPORT")


def _menu_import(self, context):
    self.layout.operator(FLIPSTUDIO_OT_import.bl_idname, icon="IMPORT")


classes = (FLIPSTUDIO_AddonPreferences, FLIPSTUDIO_OT_send, FLIPSTUDIO_OT_import)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.TOPBAR_MT_file_export.append(_menu_export)
    bpy.types.TOPBAR_MT_file_import.append(_menu_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(_menu_import)
    bpy.types.TOPBAR_MT_file_export.remove(_menu_export)
    for c in reversed(classes):
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
