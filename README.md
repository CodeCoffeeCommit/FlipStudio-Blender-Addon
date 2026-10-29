# FlipStudio Bridge (Blender add-on)

Two menu items that connect Blender and FlipStudio through files:

- **File > Export > Send to FlipStudio** exports the selected mesh objects as
  glTF binary with modifiers and geometry nodes applied, writes the file to an
  exchange folder, and launches FlipStudio on it. FlipStudio imports the file
  on start-up through its scene-importer registry (ADR-065 Amendment A).
- **File > Import > Import from FlipStudio** opens an exchange file (glTF,
  OBJ or FBX) with Blender's own importers, starting in the exchange folder.

Set the FlipStudio executable and the exchange folder under
Edit > Preferences > Add-ons > FlipStudio Bridge.

## Install

Zip the `flipstudio_bridge` folder and install it from Blender's Add-ons
preferences, or copy the folder into your Blender `scripts/addons` directory.
Blender 3.6 or newer.

## Licence

This add-on is licensed GPL-2.0-or-later, as Blender add-ons must be. It is a
separate work from FlipStudio: FlipStudio links none of it, and the two
programs exchange only files. See LICENSE. (Ticket LDC-647.)
